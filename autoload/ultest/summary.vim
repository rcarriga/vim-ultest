let s:buffer_name = "Ultest Summary"
let s:mappings = {
      \ "run": "r",
      \ "jumpto": "<CR>",
      \ "output": "o",
      \ "attach": "a",
      \ "stop": "s"
      \ }

call extend(s:mappings, g:ultest_summary_mappings)

autocmd FileType UltestSummary call <SID>CreateMappings()

function! s:CreateMappings()
  exec "nnoremap <silent><buffer> ".s:mappings["run"]." :call <SID>RunCurrent()<CR>"
  exec "nnoremap <silent><buffer> ".s:mappings["output"]." :call <SID>OpenCurrentOutput()<CR>"
  exec "nnoremap <silent><buffer> ".s:mappings["jumpto"]." :call <SID>JumpToCurrent()<CR>"
  exec "nnoremap <silent><buffer> ".s:mappings["attach"]." :call <SID>AttachToCurrent()<CR>"
  exec "nnoremap <silent><buffer> ".s:mappings["stop"]." :call <SID>StopCurrent()<CR>"
endfunction

function! s:IsOpen() abort
  return bufexists(s:buffer_name) && bufwinnr(s:buffer_name) != -1
endfunction

function! ultest#summary#jumpto() abort
  call ultest#summary#open()
  call ultest#util#goToBuffer(s:buffer_name)
endfunction

function! ultest#summary#open() abort
  if !s:IsOpen() 
    call s:OpenNewWindow()
  endif
endfunction

function! ultest#summary#close() abort
  if s:IsOpen() 
    exec bufwinnr(s:buffer_name)."close"
  endif
endfunction

function! ultest#summary#toggle() abort
  if s:IsOpen() 
    call ultest#summary#close()
  else
    call ultest#summary#open()
  endif
endfunction

function! ultest#summary#render(test) abort
  if s:IsOpen()
    call s:FullRender()
  endif
endfunction

function! s:GetFoldLevel(lnum) abort
  let l = getline(a:lnum)
  echom l
  if l == "" | return 0 | endif
  return 1
endfunction

function! s:OpenNewWindow() abort
  exec "botright vnew ".s:buffer_name." | vertical resize ".g:ultest_summary_width
  let buf_settings = {
        \ "buftype": "nofile",
        \ "bufhidden": "hide",
        \ "buflisted": 0,
        \ "swapfile": 0,
        \ "modifiable": 0,
        \ "relativenumber": 0,
        \ "number": 0,
        \ "filetype": "UltestSummary",
        \ "foldmethod": "expr",
        \ }
  for [key, val] in items(buf_settings)
    call setbufvar(s:buffer_name, "&".key, val)
  endfor
  let win_settings = {
    \ "foldtext": 'substitute(getline(v:foldstart),"\s*{{{[0-9]\s*$","","")." ▶"',
    \ "foldexpr": "len(getline(v:lnum))>1",
    \ "winfixwidth": 1
    \ }
  let win = bufwinnr(s:buffer_name)
  for [key, val] in items(win_settings)
    call setwinvar(win, "&".key, val)
  endfor
  augroup UltestSummary 
    au!
    au CursorMoved <buffer> norm! 0
  augroup END
  call s:FullRender()
  exec "norm \<C-w>p"
endfunction

function! s:FullRender() abort
  call setbufvar(s:buffer_name, "&modifiable", 1)
  call s:Clear()
  let lines = []
  let win = bufwinnr(s:buffer_name)
  for test_file in g:ultest_buffers
    let sorted_ids = getbufvar(test_file, "ultest_sorted_tests")
    let tests = getbufvar(test_file, "ultest_tests", {})
    let results = getbufvar(test_file, "ultest_results", {})
    if len(tests) == 0 | continue | endif
    let lines = lines + ["", " ".fnamemodify(test_file, ":t")]
    call matchaddpos("UltestInfo", [len(lines) - 1], 10, -1, {"window": win})
    let line_offset = len(lines)
    for index in range(len(sorted_ids))
      let test_id = sorted_ids[index]
      let test = get(tests, test_id, {})
      let result = get(results, test_id, {})
      if test == {} | continue | endif
      call add(lines, s:RenderLine(test, result, index+line_offset, win, index == len(sorted_ids) - 1))
    endfor
  endfor
  if len(lines) > 0
    call remove(lines, 0)
  endif
  if has("nvim")
    call nvim_buf_set_lines(bufnr(s:buffer_name), 0, len(lines), v:false, lines)
  else
    call setbufline(s:buffer_name, 1, lines)
  endif
  silent call deletebufline(s:buffer_name, len(lines)+1, "$")
  silent call deletebufline(s:buffer_name, len(lines)+1, "$")
  call setbufvar(s:buffer_name, "&modifiable", 0)
endfunction

function! s:RenderLine(test, result, line, window, is_last) abort
  let text = ""
  if has_key(a:result, "code")
    if a:result.code
      let highlight = "UltestFail"
    else
      let highlight = "UltestPass"
    endif
  else
    if a:test.running
      let highlight = "UltestRunning"
    else
      let highlight = "Normal"
    endif
  endif
  call matchaddpos(highlight, [[a:line, 3, len(a:test.name) + 4]], 10, -1, {"window": a:window})
  return (a:is_last ? "└" : "│")." ".a:test.name
endfunction

function! s:Clear() abort
  if bufexists(s:buffer_name)
    call clearmatches(bufwinnr(s:buffer_name))
  endif
endfunction


function! s:RunCurrent()
  let [cur_file, cur_test] = s:GetAtLine(s:GetCurrentLine())
  if cur_file == ""
    return
  elseif cur_test == ""
    call ultest#handler#run_all(cur_file)
  else
    call ultest#handler#run_single(cur_test, cur_file)
  endif
endfunction

function! s:JumpToCurrent()
  let [cur_file, cur_test] = s:GetAtLine(s:GetCurrentLine())
  if cur_file == ""
    return
  endif
  let win = bufwinnr(cur_file)
  if win == -1
    echom "Window not open for ".cur_file
    return
  else
    exec win."wincmd w"
  endif
  if cur_test != ""
    let tests = getbufvar(cur_file, "ultest_tests", {})
    let test = get(tests, cur_test, {})
    if test != {}
      exec "norm ".test["line"]."G"
    endif
  endif
endfunction

function! s:AttachToCurrent()
  let [cur_file, cur_test] = s:GetAtLine(s:GetCurrentLine())
  if cur_file == "" || cur_test == ""
    return
  else
    let test = get(getbufvar(cur_file, "ultest_tests", {}), cur_test)
    call ultest#output#attach(test)
  endif
endfunction

function! s:StopCurrent()
  let [cur_file, cur_test] = s:GetAtLine(s:GetCurrentLine())
  if cur_file == "" || cur_test == ""
    return
  else
    let test = get(getbufvar(cur_file, "ultest_tests", {}), cur_test)
    call ultest#handler#stop_test(test)
  endif
endfunction

function! s:OpenCurrentOutput()
  let [cur_file, cur_test] = s:GetAtLine(s:GetCurrentLine())
  if cur_file == "" || cur_test == ""
    return
  else
    let test = get(getbufvar(cur_file, "ultest_tests", {}), cur_test)
    call ultest#output#open(test)
  endif
endfunction

""
" Returns a tuple of
" 1) Currently selected test file (or "")
" 2) Currently selected test (or "")
function! s:GetCurrentLine()
  " Increase by one to account for no space at top
  if !s:IsOpen() | return 0 | endif
  return getbufinfo(s:buffer_name)[0]["lnum"]
endfunction

function! s:GetAtLine(line)
  let lines_to_go = a:line
  for test_file in g:ultest_buffers
    let sorted_ids = getbufvar(test_file, "ultest_sorted_tests")
    if lines_to_go == 1
      return [test_file, ""]
    endif
    let lines_to_go -= 1
    if lines_to_go <= len(sorted_ids)
      return [test_file, sorted_ids[lines_to_go - 1]]
    endif
    let lines_to_go -= len(sorted_ids) + 1
  endfor
  return ["", ""]
endfunction
