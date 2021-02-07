let s:buffer_name = "Ultest Summary"

function! s:IsOpen() abort
  return bufexists(s:buffer_name) && bufwinnr(s:buffer_name) != -1
endfunction

function! ultest#summary#goto() abort
  call ultest#summary#open()
  call ultest#util#goToBuffer(s:buffer_name)
endfunction

function! ultest#summary#render(test) abort
  if s:IsOpen()
    call s:FullRender()
  endif
endfunction

function! ultest#summary#open() abort
  if s:IsOpen() | return | endif
  exec "botright vnew ".s:buffer_name." | vertical resize 50"
  call setwinvar(bufwinnr(s:buffer_name), "&winfixwidth", 1)
  let buf_settings = {
    \ "buftype": "nofile",
    \ "bufhidden": "hide",
    \ "buflisted": 0,
    \ "swapfile": 0,
    \ "modifiable": 0,
    \ "filetype": "ultestsummary",
    \ "relativenumber": 0,
    \ "number": 0
    \ }
  for [key, val] in items(buf_settings)
    call setbufvar(s:buffer_name, "&".key, val)
  endfor
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
    let lines = lines + ["", "Test File: ".fnamemodify(test_file, ":t")]
    call matchaddpos("UltestInfo", [len(lines)], 10, -1, {"window": win})
    let line_offset = len(lines)+1
    for index in range(len(sorted_ids))
      let test_id = sorted_ids[index]
      let test = get(tests, test_id, {})
      let result = get(results, test_id, {})
      if test == {} | echom string(test_id) | continue | endif
      call add(lines, s:RenderLine(test, result, index+line_offset, win))
    endfor
  endfor
  call setbufline(s:buffer_name, 1, lines)
  silent call deletebufline(s:buffer_name, len(lines)+1, "$")
  call setbufvar(s:buffer_name, "&modifiable", 0)
endfunction

function! s:RenderLine(test, result, line, window) abort
  let text = ""
  if has_key(a:result, "code")
    if a:result.code
      let sign = g:ultest_fail_sign
      let highlight = "UltestFail"
    else
      let sign = g:ultest_pass_sign
      let highlight = "UltestPass"
    endif
  else
    if a:test.running
      let sign = g:ultest_running_sign
      let highlight = "UltestRunning"
    else
      let sign = " "
      let highlight = "Normal"
    endif
  endif
  call matchaddpos(highlight, [a:line], 10, -1, {"window": a:window})
  return " ".sign." ".a:test.name
endfunction

function! s:Clear() abort
  if bufexists(s:buffer_name)
    call clearmatches(bufwinnr(s:buffer_name))
  endif
endfunction
