if get(g:, "ultest_loaded")
  finish
endif
let g:ultest_loaded = 1

let s:strategy = "ultest"
let g:test#custom_strategies = get(g:, "test#custom#strategies", {})
let g:test#custom_strategies[s:strategy] = function('ultest#handler#strategy')
let g:ultest_buffers = []

""
" @section Introduction
" @order introduction config commands functions highlights mappings debugging
" @stylized vim-ultest
"
" The ultimate testing plugin for Vim/NeoVim
"
" Running tests should be as quick and painless as possible.
" [vim-test](https://github.com/janko/vim-test) is a very powerful and extensive testing plugin, but it can be cumbersome to configure and lacks some features to make it feel like an integrated piece of your editor.
" Rather than replacing vim-test altogether, vim-ultest makes it even better while maintaining the ability to use your existing configuration.
" If you're already using vim-test then switching to vim-ultest is as easy as installing and... well, that's pretty much it.
"
" The goal behind vim-ultest is to make running tests as seamless as possible.
"
" * Tests are displayed individually so that any errors can be addressed individually.
" * Tests are run in seperate threads (not just asynchronously on the same thread) so your Vim session will never be blocked.
" * When tests are complete, results can be viewed immediately or on command.
" * Utilise the existing power of vim-test by extending upon it.

"

""
" @section Highlights
"
" Define the following highlight groups to override their values by copying
" these commands and changing their colours/attributes.
"
" hi UltestPass ctermfg=Green guifg=#96F291
"
" hi UltestFail ctermfg=Red guifg=#F70067
"
" hi UltestRunning ctermfg=Yellow guifg=#FFEC63
"
" hi UltestBorder ctermfg=Red guifg=#F70067
"
" hi UltestSummaryInfo ctermfg=cyan guifg=#00F1F5 gui=bold cterm=bold
"
" hi link UltestSummaryFile UltestSummaryInfo
"
" hi link UltestSummaryNamespace UltestSummaryInfo

hi default UltestPass ctermfg=Green guifg=#96F291
hi default UltestFail ctermfg=Red guifg=#F70067
hi default UltestRunning ctermfg=Yellow guifg=#FFEC63
hi default UltestDefault ctermfg=Grey guifg=#8B8B8B
hi default UltestBorder ctermfg=Red guifg=#F70067
hi default UltestSummaryInfo ctermfg=cyan guifg=#00F1F5
hi default link UltestSummaryFile UltestSummaryInfo
hi default link UltestSummaryNamespace UltestSummaryInfo

""
" Number of workers that are used for running tests.
" (default: 2)
let g:ultest_max_threads = get(g:, "ultest_max_threads", 2)

""
" Show failed outputs when completed run.
" (default: 1)
let g:ultest_output_on_run = get(g:, "ultest_output_on_run", 1)

""
" Show failed outputs when cursor is on first line of test/namespace.
"
" This relies on the 'updatetime' setting which by default is 4 seconds.
" A longer 'updatetime' will mean the window takes longer to show
" automatically but a shorter time means (Neo)Vim will write to disk
" much more often which can degrade SSDs over time and cause slowdowns on HDDs.
"
" Due to how Vim handles terminal popups, this is disabled by default as it
" can be annoying.
" (default: has("nvim"))
let g:ultest_output_on_line =  get(g:, "ultest_output_on_line", has("nvim"))

""
" Use unicode icons
" (default: 1)
let g:ultest_icons = get(g:, "ultest_icons", 1)

""
" Number of rows for terminal size where tests are run (default: 0)
" Set to zero to not instruct runner on size of terminal.
" Note: It is up to the test runner to respect these bounds
let g:ultest_output_rows = get(g:, "ultest_output_rows", 0)

""
" Number of columns for terminal size where tests are run (default: 0)
" Set to zero to not instruct runner on size of terminal.
" Note: It is up to the test runner to respect these bounds
let g:ultest_output_cols = get(g:, "ultest_output_cols", 0)

"" Enable sign/virtual text processor for tests.
" (default: 1)
let g:ultest_show_in_file = get(g:, "ultest_show_in_file", 1)

""
" Use virtual text (if available) instead of signs to show test results in file.
" (default: 0)
let g:ultest_virtual_text = get(g:, "ultest_virtual_text", 0)

""
" Sign for passing tests.
" (default: g:ultest_icons ? "" : "O")
let g:ultest_pass_sign = get(g:, "ultest_pass_sign", g:ultest_icons ? "" : "O")
""
" Sign for failing tests.
" (default: g:ultest_icons ? "" : "X")
let g:ultest_fail_sign = get(g:, "ultest_fail_sign", g:ultest_icons ? "" : "X")

""
" Sign for running tests (string)
" (default: g:ultest_icons ? "" : ">")
let g:ultest_running_sign = get(g:, "ultest_running_sign", g:ultest_icons ? "" : ">")

""
" Sign for tests not yet run (string)
" (default: g:ultest_icons ? "" : "~")
let g:ultest_not_run_sign = get(g:, "ultest_not_run_sign", g:ultest_icons ? "" : "~")

""
" Virtual text for passing tests (string)
" (default: g:ultest_icons? "●":"Passing")
let g:ultest_pass_text = get(g:, "ultest_pass_text", g:ultest_icons? "●":"Passing")
""
" Virtual text for failing tests (string)
" (default: g:ultest_icons? "●":"Failing")
let g:ultest_fail_text = get(g:, "ultest_fail_text", g:ultest_icons? "●":"Failing")
""
" Virtual text for passing tests (string)
" (default: g:ultest_icons? "●":"Running")
let g:ultest_running_text = get(g:, "ultest_running_text", g:ultest_icons? "●":"Running")

""
" Width of the summary window
" (default: 50)
let g:ultest_summary_width = get(g:, "ultest_summary_width", 50)

""
" A function name to call before running any tests in a file.
" Receives the relative file path as an argument.
let g:ultest_pre_run = get(g:, "ultest_pre_run")

""
" Width of the attach window
" Some test runners don't output anyting until finished (e.g. Jest) so the
" attach window can't figure out a good width. Use this to hardcode a size.
" (default: 0)
let g:ultest_attach_width = get(g:, "ultest_attach_width", 0)

""
" Custom list of receivers for position events.
" This is experimental and could change!
" Receivers are dictionaries with any of the following keys:
"
" 'new': A function which takes a new position which has been discovered.
"
" 'move': A function which takes a position which has been moved.
"
" 'replace': A function which takes a position which has previously been cleared but has been replaced.
"
" 'start': A function which takes a position which has been run.
"
" 'exit': A function which takes a position result once it has completed.
"
" 'clear': A function which takes a position which has been removed for some
" reason.
"
" Positions can be either a file, namespace or test, distinguished with a
" 'type' key.
"
let g:ultest_custom_processors = get(g:, "ultest_custom_processors", [])
let g:ultest#processors = [
      \   {
      \       "condition": g:ultest_show_in_file,
      \       "start": "ultest#signs#start",
      \       "clear": "ultest#signs#unplace",
      \       "exit": "ultest#signs#process",
      \       "move": "ultest#signs#move",
      \       "replace": "ultest#signs#process"
      \   },
      \   {
      \       "new": "ultest#summary#render",
      \       "start": "ultest#summary#render",
      \       "clear": "ultest#summary#render",
      \       "exit": "ultest#summary#render",
      \       "move": "ultest#summary#render",
      \       "replace": "ultest#summary#render"
      \   },
      \] + get(g:, "ultest_custom_processors", [])

""
" Custom patterns for identifying positions. This dictionary should use the keys
" in the form '<language>' or '<language>#<runner>'. The values should be a
" dictionary with the following keys:
"
" 'test': A list a python-style regex patterns that can each indentify tests
" in a line of code
"
" 'namepsace': A list of python-style regex patterns that can idenitfy test
" namespaces (e.g. Classes).
"
" If you find a missing language that requires you to set this value,
" considering onpening an issue/PR to make it available to others.
let g:ultest_custom_patterns = get(g:, "ultest_custom_patterns", {})

let g:ultest_patterns = extend({
      \ "elixir#exunit": {
        \ 'test': ["^\\s*test\\s+['\"](.+)['\"]\\s+do"],
      \}
    \ }, g:ultest_custom_patterns)

""
" Key mappings for the summary window (dict)
" Possible values:
"
" 'run': (default "r") Runs the test currently selected or whole file if file name is selected.
"
" 'jumpto': (default "<CR>") Jump to currently selected test in its file.
"
" 'output': (default "o") Open the output to the current test if failed.
"
" 'attach': (default "a") Attach to the running process of the current test.
"
" 'stop': (default "s") Stop the running process of the current test.
"
" 'next_fail': (default "<S-j>") Jump down to the next fail.
"
" 'prev_fail': (default "<S-k>") Jump up to the next fail.
"
" The summary window also defines folds for each files and namespaces so they
" can be hidden as desired using the regular fold mappings.
let g:ultest_summary_mappings = get(g:, "ultest_summary_mappings", {
      \ "run": "r",
      \ "jumpto": "<CR>",
      \ "output": "o",
      \ "attach": "a",
      \ "stop": "s",
      \ "next_fail": "<S-j>",
      \ "prev_fail": "<S-k>"
      \ })

call sign_define("test_pass", {"text":g:ultest_pass_sign, "texthl": "UltestPass"})
call sign_define("test_fail", {"text":g:ultest_fail_sign, "texthl": "UltestFail"})
call sign_define("test_running", {"text":g:ultest_running_sign, "texthl": "UltestRunning"})

""
" Run all tests in the current file
" Some runners can be run as a single command if the output can be parsed to
" gain results. Otherwise, each test is run as a single command.
"
" Running as a single command can significanly improve performance, so if your
" runner is not yet supported please open an issue with sample output! Check
" the repo wiki for an updated list of runners.
command! Ultest call ultest#run_file({"pre_run": g:ultest_pre_run})

""
" Run nearest position in the current file
" If no position is found it will attempt to run the entire file
command! UltestNearest call ultest#run_nearest({"pre_run": g:ultest_pre_run})

""
" Debug the current file with nvim-dap
command! UltestDebug call ultest#run_file({"pre_run": g:ultest_pre_run, "runner": "nvim-dap"})

""
" Debug the nearest position with nvim-dap
command! UltestDebugNearest call ultest#run_nearest({"pre_run": g:ultest_pre_run, "runner": "nvim-dap"})

""
" Show the output of the nearest position in the current file
command! UltestOutput call ultest#output#open(ultest#handler#get_nearest_test(line("."), expand("%:."), v:false))

""
" Attach to the running process of a position to be able to send input and read
" output as it runs. This is useful for debugging
command! UltestAttach call ultest#output#attach(ultest#handler#get_nearest_test(line("."), expand("%:."), v:false))

""
" Stop all running jobs for the current file
command! UltestStop call ultest#stop_file()

""
" Stop any running jobs and results for the nearest position
command! UltestStopNearest call ultest#stop_nearest()

""
" Toggle the summary window between open and closed
command! UltestSummary call ultest#summary#toggle()

""
" Open the summary window
command! UltestSummaryOpen call ultest#summary#open()

""
" Close the summary window
command! UltestSummaryClose call ultest#summary#close()

""
" @section Mappings
"
" <Plug>(ultest-next-fail)	 Jump to next failed test.
"
" <Plug>(ultest-prev-fail)	 Jump to previous failed test.
"
" <Plug>(ultest-run-file) 	 Run all tests in a file.
"
" <Plug>(ultest-run-nearest)	 Run test closest to the cursor.
"
" <Plug>(ultest-summary-toggle)	 Toggle the summary window between open and closed
"
" <Plug>(ultest-summary-jump)	 Jump to the summary window (opening if it isn't already)
"
" <Plug>(ultest-output-show) 	 Show error output of the nearest test. (Will jump to popup window in Vim)
"
" <Plug>(ultest-output-jump) 	 Show error output of the nearest test. (Same behabviour as <Plug>(ultest-output-show) in Vim)
"
" <Plug>(ultest-attach) 	 Attach to the nearest test's running process.
"
" <Plug>(ultest-stop-file) 	 Stop all running jobs for current file
"
" <Plug>(ultest-stop-nearest) 	 Stop any running jobs for nearest test
"
" <Plug>(ultest-debug)	  Debug the current file with nvim-dap
"
" <Plug>(ultest-debug-nearest)	  Debug the nearest test with nvim-dap

nnoremap <silent><Plug>(ultest-next-fail) :call ultest#positions#next()<CR>
nnoremap <silent><Plug>(ultest-prev-fail) :call ultest#positions#prev()<CR>
nnoremap <silent><Plug>(ultest-run-file) :Ultest<CR>
nnoremap <silent><Plug>(ultest-run-nearest) :UltestNearest<CR>
nnoremap <silent><Plug>(ultest-summary-toggle) :UltestSummary<CR>
nnoremap <silent><Plug>(ultest-summary-jump) :call ultest#summary#jumpto()<CR>
nnoremap <silent><Plug>(ultest-output-show) :UltestOutput<CR>
nnoremap <silent><Plug>(ultest-output-jump) :call ultest#output#jumpto()<CR>
nnoremap <silent><Plug>(ultest-attach) :UltestAttach<CR>
nnoremap <silent><Plug>(ultest-stop-file) :UltestStop<CR>
nnoremap <silent><Plug>(ultest-stop-nearest) :UltestStop<CR>
nnoremap <silent><Plug>(ultest-debug) :UltestDebug<CR>
nnoremap <silent><Plug>(ultest-debug-nearest) :UltestDebugNearest<CR>

if g:ultest_output_on_line
  augroup UltestOutputOnLine
    au!
    au CursorHold * call ultest#output#open(ultest#handler#get_nearest_test(line("."), expand("%:."), v:true))
  augroup END
endif
let s:monitored = {}

function! s:MonitorFile(file) abort
  if has_key(s:monitored, a:file)
    return
  end
  try
    if !test#test_file(a:file)
      let s:monitored[a:file] = v:false
      return 
    endif
  catch /.*/
    " vim-test throws error on new test files that don't exist in fs. See #30
  endtry
  let buffer = bufnr(a:file)
  call ultest#handler#update_positions(a:file)
  exec 'au BufWrite <buffer='.buffer.'> call ultest#handler#update_positions("'.a:file.'")'
  exec 'au BufUnload <buffer='.buffer.'> au! * <buffer='.buffer'>'
  let s:monitored[a:file] = v:true
endfunction

augroup UltestPositionUpdater
  au!
  au BufEnter * call <SID>MonitorFile(expand("<afile>"))
  if !has("nvim")
    au VimEnter * call <SID>MonitorFile(expand("<afile>"))
  endif
augroup END

if !has("vim_starting")
  " Avoids race condition https://github.com/neovim/pynvim/issues/341
  call ultest#handler#get_attach_script("")
  for open_file in split(execute("buffers"), "\n")
    let file_name = matchstr(open_file, '".\+"')
    if file_name != ""
      call s:MonitorFile(file_name[1:-2])
    endif
  endfor
end


""
" @section Debugging
"
" vim-ultest supports debugging through nvim-dap. Due to how debugging
" configurations can vary greatly between users and projects, some
" configuration is required for test debugging to work.
"
" You must provide a way to build a suitable nvim-dap confiuration to run a
" test, given the original command for the test. The command is given in the
" form of a list of strings. The returned table should contain a 'dap' entry
" which will be provided to nvim-dap's 'run' function.
"
" For example with a python test using the adapter defined in nvim-dap-python:
" >
"   function(cmd)
"     -- The command can start with python command directly or an env manager
"     local non_modules = {'python', 'pipenv', 'poetry'}
"     -- Index of the python module to run the test.
"     local module
"     if vim.tbl_contains(non_modules, cmd[1]) then
"       module = cmd[3]
"     else
"       module = cmd[1]
"     end
"     -- Remaining elements are arguments to the module
"     local args = vim.list_slice(cmd, module_index + 1)
"     return {
"       dap = {
"         type = 'python',
"         request = 'launch',
"         module = module,
"         args = args
"       }
"     }
"   end,
" <
" This will separate out the module name and arguments to provide to the
" nvim-dap-python adapter.
"
" To provide this to vim-ultest, call the setup function, providing a table
" with a 'builders' entry, with your language mapped to the builder. If you require
" multiple runners, the key can be in the form of '<language>#<runner>'
" (Example: 'python#pytest')
" >
"   require("ultest").setup({
"     builders = {
"       ['python#pytest'] = function (cmd)
"         ...
"       end
"     }
"   })
" <
"
" Some adapters don't provide an exit code when running tests, such as
" vscode-go. This causes vim-ultest to never receive a result. To work around
" this, you can provide a 'parse_result' entry in the returned table of your
" config builder function which will receive the output of the program as a
" list of lines. You can then return an exit code for the test.
" For example with vscode-go and gotest, the final line will state 'FAIL' on a
" failed test.
" >
"   ["go#gotest"] = function(cmd)
"     local args = {}
"     for i = 3, #cmd - 1, 1 do
"       local arg = cmd[i]
"       if vim.startswith(arg, "-") then
"         -- Delve requires test flags be prefix with 'test.'
"         arg = "-test." .. string.sub(arg, 2)
"       end
"       args[#args + 1] = arg
"     end
"     return {
"       dap = {
"         type = "go",
"         request = "launch",
"         mode = "test",
"         program = "${workspaceFolder}",
"         dlvToolPath = vim.fn.exepath("dlv"),
"         args = args
"       },
"       parse_result = function(lines)
"         return lines[#lines] == "FAIL" and 1 or 0
"       end
"     }
"   end
" < 
