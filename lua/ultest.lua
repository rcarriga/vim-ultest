local M = {}

local builders = {}

local function dap_run_test(test, build_config)
  local dap = require("dap")
  local cmd = vim.fn["ultest#adapter#build_cmd"](test, "nearest")

  local output_name = vim.fn["tempname"]()

  local handler_id = "ultest_" .. test.id

  local user_config = build_config(cmd)

  local exit_handler = function(_, info)
    io.close()
    vim.fn["ultest#handler#external_result"](test.id, test.file, info.exitCode)
  end
  local terminated_handler = function()
    if user_config.parse_result then
      local lines = {}
      for line in io.lines(output_name) do
        lines[#lines + 1] = line
      end
      local exit_code = user_config.parse_result(lines)
      vim.fn["ultest#handler#external_result"](test.id, test.file, exit_code)
    end
  end

  local output_handler = function(_, body)
    if vim.tbl_contains({"stdout", "stderr"}, body.category) then
      io.write(body.output)
      io.flush()
    end
  end

  require("dap").run(
    user_config.dap,
    {
      before = function(config)
        local output_file = io.open(output_name, "w")
        io.output(output_file)
        vim.fn["ultest#handler#external_start"](test.id, test.file, output_name)
        dap.listeners.after.event_output[handler_id] = output_handler
        dap.listeners.before.event_terminated[handler_id] = terminated_handler
        dap.listeners.after.event_exited[handler_id] = exit_handler
        return config
      end,
      after = function()
        dap.listeners.after.event_exited[handler_id] = nil
        dap.listeners.before.event_terminated[handler_id] = nil
        dap.listeners.after.event_output[handler_id] = nil
      end
    }
  )
end

local function get_builder(test, config)
  local builder =
    config.build_config or builders[vim.fn["ultest#adapter#get_runner"](test.file)] or
    builders[vim.fn["getbufvar"](test.file, "&filetype")]

  if builder == nil then
    print("Unsupported runner, need to provide a customer nvim-dap config builder")
    return nil
  end

  if config.override_config ~= nil then
    builder = function(cmd)
      return config.override_config(builder(cmd))
    end
  end

  return builder
end

-- Run the nearest test to a position using nvim-dap
--
-- @param config {table | nil}
--   Optional keys:
--     'file': File to search in, defaults to current file.
--     'line': Line to search from, defaults to current line.
--     'build_config': Function to receive the test command in a list of
--                     strings, to return a nvim-dap configuration. Required
--                     if there is no default builder for the test runner
function M.dap_run_nearest(config)
  config = config or {}
  local file = config.file
  local line = config.line
  if file == nil then
    file = vim.fn["expand"]("%:.")
  end

  if line == nil then
    line = vim.fn["getbufinfo"](file)[1]["lnum"]
  end

  local test = vim.fn["ultest#handler#get_nearest_test"](line, file, false)
  if test == vim.NIL then
    return
  end
  local builder = get_builder(test, config)
  if builder == nil then
    return
  end

  dap_run_test(test, builder)
end

function M.setup(config)
  builders = config.builders
end

return M
