local M = {}

local api = vim.api
local diag = vim.diagnostic

local tracking_namespace = api.nvim_create_namespace("_ultest_diagnostic_tracking")
local diag_namespace = api.nvim_create_namespace("ultest_diagnostic")

---@class NvimDiagnostic
---@field lnum integer The starting line of the diagnostic
---@field end_lnum integer The final line of the diagnostic
---@field col integer The starting column of the diagnostic
---@field end_col integer The final column of the diagnostic
---@field severity string The severity of the diagnostic |vim.diagnostic.severity|
---@field message string The diagnostic text
---@field source string The source of the diagnostic

---@class UltestTest
---@field type "test" | "file" | "namespace"
---@field id string
---@field name string
---@field file string
---@field line integer
---@field col integer
---@field running integer
---@field namespaces string[]
--
---@class UltestResult
---@field id string
---@field file string
---@field code integer
---@field output string
---@field error_message string[] | nil
---@field error_line integer | nil

local marks = {}
local error_code_lines = {}
local attached_buffers = {}

local function init_mark(bufnr, result)
  marks[result.id] = api.nvim_buf_set_extmark(
    bufnr,
    tracking_namespace,
    result.error_line - 1,
    0,
    { end_line = result.error_line }
  )
  error_code_lines[result.id] = api.nvim_buf_get_lines(
    bufnr,
    result.error_line - 1,
    result.error_line,
    false
  )[1]
end

local function create_diagnostics(bufnr, results)
  local diagnostics = {}
  for _, result in pairs(results) do
    if not marks[result.id] then
      init_mark(bufnr, result)
    end
    local mark = api.nvim_buf_get_extmark_by_id(bufnr, tracking_namespace, marks[result.id], {})
    local mark_code = api.nvim_buf_get_lines(bufnr, mark[1], mark[1] + 1, false)[1]
    if mark_code == error_code_lines[result.id] then
      diagnostics[#diagnostics + 1] = {
        lnum = mark[1],
        col = 0,
        message = table.concat(result.error_message, "\n"),
        source = "ultest",
      }
    end
  end
  return diagnostics
end

local function draw_buffer(file)
  local bufnr = vim.fn.bufnr(file)
  ---@type UltestResult[]
  local results = api.nvim_buf_get_var(bufnr, "ultest_results")

  local valid_results = vim.tbl_filter(function(result)
    return type(result) == "table" and result.error_line and result.error_message
  end, results)

  local diagnostics = create_diagnostics(bufnr, valid_results)

  diag.set(diag_namespace, bufnr, diagnostics)
end

local function clear_mark(test)
  local bufnr = vim.fn.bufnr(test.file)
  local mark_id = marks[test.id]
  if not mark_id then
    return
  end
  marks[test.id] = nil
  api.nvim_buf_del_extmark(bufnr, tracking_namespace, mark_id)
end

local function attach_to_buf(file)
  local bufnr = vim.fn.bufnr(file)
  attached_buffers[file] = true

  vim.api.nvim_buf_attach(bufnr, false, {
    on_lines = function()
      draw_buffer(file)
    end,
  })
end

local function get_files(tests)
  local files = {}
  for _, test in pairs(tests) do
    if not files[test.file] then
      files[test.file] = true
    end
  end
  return files
end

---@param tests UltestTest[]
function M.clear(tests)
  local files = get_files(tests)
  for file, _ in pairs(files) do
    draw_buffer(file)
  end
end

---@param results UltestResult[]
function M.exit(results)
  for _, result in pairs(results) do
    clear_mark(result)
  end
  local files = get_files(results)
  for file, _ in pairs(files) do
    if not attached_buffers[file] then
      attach_to_buf(file)
    end
    draw_buffer(file)
  end
end

---@param tests UltestTest[]
function M.delete(tests)
  for _, test in pairs(tests) do
    clear_mark(test)
  end
  local files = get_files(tests)

  for file, _ in pairs(files) do
    draw_buffer(file)
  end
end

return M
