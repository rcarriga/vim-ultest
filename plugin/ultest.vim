let s:strategy = "ultest"
let g:test#custom_strategies = get(g:, "test#custom#strategies", {})
let g:test#custom_strategies[s:strategy] = function('ultest#handler#strategy')
let g:ultest_buffers = []

""
" @section Introduction
" @order introduction config commands highlights mappings
" @stylized Ultest
"
" The ultimate testing plugin for Vim/NeoVim
"
" Running tests should be as quick and painless as possible.
" [vim-test](https://github.com/janko/vim-test) is a very powerful and extensive testing plugin, but it can be cumbersome to configure and lacks some features to make it feel like an integrated piece of your editor.
" Rather than replacing vim-test altogether, Ultest makes it even better while maintaining the ability to use your existing configuration.
" If you're already using vim-test then switching to Ultest is as easy as installing and... well, that's pretty much it.
"
" The goal behind Ultest is to make running tests as seamless as possible.
"
" * Tests are run individually so that any errors can be addressed individually.
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
" hi UltestInfo ctermfg=cyan guifg=#00F1F5 cterm=bold gui=bold

hi default UltestPass ctermfg=Green guifg=#96F291
hi default UltestFail ctermfg=Red guifg=#F70067
hi default UltestRunning ctermfg=Yellow guifg=#FFEC63
hi default UltestBorder ctermfg=Red guifg=#F70067
hi default UltestInfo ctermfg=cyan guifg=#00F1F5 cterm=bold gui=bold

""
" Number of workers that are used for running and processing tests.
" Set to 0 to use number of cpu cores - 1 (to avoid blocking main thread)
" (default: 0)
let g:ultest_max_threads = get(g:, "ultest_max_threads", 0)

""
" Enable positions processor for tests to allow jumping between tests.
" (default: 1)
let g:ultest_positions = get(g:, "ultest_positions", 1)

""
" Show failed outputs when completed run.
" (default: 1)
let g:ultest_output_on_run = get(g:, "ultest_output_on_run", 1)

""
" Show failed outputs when cursor is on first line of test.
" Due to how Vim handles terminal popups, this is disabled by default as it
" can be annoying.
" (default: has("nvim"))
let g:ultest_output_on_line =  get(g:, "ultest_output_on_line", has("nvim"))

""
" Use unicode icons for results signs/virtual text.
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
" (default: g:ultest_icons ? "●" : "O")
let g:ultest_pass_sign = get(g:, "ultest_pass_sign", g:ultest_icons ? "●" : "O")
""
" Sign for failing tests.
" (default: g:ultest_icons ? "●" : "X")
let g:ultest_fail_sign = get(g:, "ultest_fail_sign", g:ultest_icons ? "●" : "X")

""
" Sign for running tests (string)
" (default: g:ultest_icons ? "●" : "X")
let g:ultest_running_sign = get(g:, "ultest_running_sign", g:ultest_icons ? "●" : "X")

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
" Custom list of receivers for test events.
" This is experimental and could change!
" Receivers are dictionaries with any of the following keys:
" 'new': A function which takes a new test which has been discovered.
" 'move': A function which takes a test which has been moved.
" 'replace': A function which takes a test which has previously been cleared but has been replaced.
" 'start': A function which takes a test which has been run.
" 'exit': A function which takes a test result once it has completed.
" 'clear': A function which takes a test which has been removed for some
" reason.
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
" Key mappings for the summary window (dict)
" Possible values:
" "run" (default "r"): Runs the test currently selected or whole file if file name is selected.
" "jumpto" (default "<CR>"): Jump to currently selected test.
" "output" (default "o"): Open the output to the current test if failed.
let g:ultest_summary_mappings = get(g:, "ultest_summary_mappings", {
      \ "run": "r",
      \ "jumpto": "<CR>",
      \ "output": "o"
      \ })

""
" Run all tests in the current file
command! -bar Ultest call ultest#handler#run_all(expand("%"))

""
" Run nearest test in the current file
command! -bar UltestNearest call ultest#handler#run_nearest(line("."), expand("%"))

""
" Show the output of the nearest test in the current file
command! -bar UltestOutput call ultest#output#open(ultest#handler#get_nearest_test(line("."), expand("%"), v:false))

""
" Toggle the summary window between open and closed
command! -bar UltestSummary call ultest#summary#toggle()

""
" Open the summary window
command! -bar UltestSummaryOpen call ultest#summary#open()

""
" Close the summary window
command! -bar UltestSummaryClose call ultest#summary#close()

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

nnoremap <silent><Plug>(ultest-next-fail) :call ultest#positions#next()<CR>
nnoremap <silent><Plug>(ultest-prev-fail) :call ultest#positions#prev()<CR>
nnoremap <silent><Plug>(ultest-run-file) :Ultest<CR>
nnoremap <silent><Plug>(ultest-run-nearest) :UltestNearest<CR>
nnoremap <silent><Plug>(ultest-summary-toggle) :UltestSummary<CR>
nnoremap <silent><Plug>(ultest-summary-jump) :call ultest#summary#jumpto()<CR>
nnoremap <silent><Plug>(ultest-output-show) :UltestOutput<CR>
nnoremap <silent><Plug>(ultest-output-jump) :call ultest#output#jumpto()<CR>

" Workaround to function not registering correctly sometimes
" Seems to be similar to https://github.com/neovim/pynvim/issues/386
" call ultest#handler#get_positions(expand("%"))

if g:ultest_output_on_line
  augroup UltestOutputOnLine
    au!
    au CursorHold * call ultest#output#open(ultest#handler#get_nearest_test(line("."), expand("%"), v:true))
  augroup END
endif

augroup UltestCleanup
  au!
  au BufUnload * call ultest#handler#clear_all(expand("<afile>"))
augroup END

augroup UltestPositionUpdater
  au!
  au BufWrite,BufEnter *test* call ultest#handler#update_positions(expand("<afile>"))
augroup END


call sign_define("test_pass", {"text":g:ultest_pass_sign, "texthl": "UltestPass"})
call sign_define("test_fail", {"text":g:ultest_fail_sign, "texthl": "UltestFail"})
call sign_define("test_running", {"text":g:ultest_running_sign, "texthl": "UltestRunning"})

