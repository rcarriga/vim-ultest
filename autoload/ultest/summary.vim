let s:buffer_name = "Ultest Summary"
let s:test_line_map = {}
let s:mappings = {
      \ "run": "r",
      \ "jumpto": "<CR>",
      \ "output": "o",
      \ "attach": "a",
      \ "stop": "s",
      \ "next_fail": "<S-j>",
      \ "prev_fail": "<S-k>",
      \ }

call extend(s:mappings, g:ultest_summary_mappings)

autocmd FileType UltestSummary call <SID>CreateMappings()

function! s:CreateMappings()
  exec "nnoremap <silent><buffer> ".s:mappings["run"]." :call <SID>RunCurrent()<CR>"
  exec "nnoremap <silent><buffer> ".s:mappings["output"]." :call <SID>OpenCurrentOutput()<CR>"
  exec "nnoremap <silent><buffer> ".s:mappings["jumpto"]." :call <SID>JumpToCurrent()<CR>"
  exec "nnoremap <silent><buffer> ".s:mappings["attach"]." :call <SID>AttachToCurrent()<CR>"
  exec "nnoremap <silent><buffer> ".s:mappings["stop"]." :call <SID>StopCurrent()<CR>"
  exec "nnoremap <silent><buffer> ".s:mappings["next_fail"]." :call <SID>JumpToFail(1)<CR>"
  exec "nnoremap <silent><buffer> ".s:mappings["prev_fail"]." :call <SID>JumpToFail(-1)<CR>"
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
    call s:RenderSummary()
  endif
endfunction

function! s:GetFoldLevel(lnum) abort
  let l = getline(a:lnum)
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
    " au CursorMoved <buffer> norm! 0
  augroup END
  call s:RenderSummary()
  exec "norm \<C-w>p"
endfunction

function! Render()
  call s:RenderSummary()
endfunction

function! s:RenderSummary() abort
  call setbufvar(s:buffer_name, "&modifiable", 1)
  call s:Clear()
  let lines = []
  let matches = []
  let win = bufwinnr(s:buffer_name)
  let s:test_line_map = {}
  for test_file in g:ultest_buffers
    let structure = getbufvar(test_file, "ultest_file_structure")
    let tests = getbufvar(test_file, "ultest_tests", {})
    let results = getbufvar(test_file, "ultest_results", {})
    let state = {"lines": lines, "matches": matches, "tests": tests, "results": results }
    call s:RenderGroup("", structure, 0, state)
    if test_file != g:ultest_buffers[-1]
      call add(lines, "")
    endif
  endfor
  if has("nvim")
    call nvim_buf_set_lines(bufnr(s:buffer_name), 0, len(lines), v:false, lines)
  else
    call setbufline(s:buffer_name, 1, lines)
  endif
  for mch in matches
    call matchaddpos(mch[0], [mch[1]], 10, -1, {"window": win})
  endfor
  silent call deletebufline(s:buffer_name, len(lines)+1, "$")
  call setbufvar(s:buffer_name, "&modifiable", 0)
endfunction

function! s:RenderGroup(root_prefix, group, indent, group_state) abort
  let state = a:group_state
  let root = a:group[0]
  call s:RenderGroupMember(a:root_prefix, root, state)
  for index in range(1, len(a:group) - 2)
    let member = a:group[index]
    if type(member) == v:t_dict
      call s:RenderGroupMember(repeat(" ", a:indent).."  ", member, state)
    else
      call s:RenderGroup(repeat(" ", a:indent).."  ", member, a:indent+2, state)
    endif
  endfor
  let member = a:group[-1]
  if type(member) == v:t_dict
    call s:RenderGroupMember(repeat(" ", a:indent).."  ", member, state)
  else
    call s:RenderGroup(repeat(" ", a:indent).."  ", member, a:indent+2, state)
  endif
endfunction

function! s:RenderGroupMember(prefix, member, group_state) abort
  let state = a:group_state
  if a:member.type == "test"
    let test = get(state.tests, a:member.id, {})
    if test != {}
      let result = get(state.results, a:member.id, {})
      call s:RenderTest(a:prefix, test, result, state)
    endif
  elseif a:member.type == "namespace"
    let namespace = get(state.tests, a:member.id, {})
    if namespace != {}
      call s:RenderNamespace(a:prefix, namespace, state)
    endif
  else
    call s:RenderFile(a:prefix, a:member, state)
  endif
endfunction

function! s:RenderTest(prefix, test, result, group_state) abort
  let text = ""
  if has_key(a:result, "code")
    let highlight = a:result.code ? "UltestFail" : "UltestPass"
    let icon = a:result.code ? " ": " "
  else
    let icon = a:test.running ? " ": " "
    let highlight = a:test.running ? "UltestRunning" : "UltestDefault"
  endif
  call add(a:group_state.lines, a:prefix..icon..a:test.name)
  call add(a:group_state.matches, [highlight, [len(a:group_state.lines), len(a:prefix) + 1, 1]])
  let s:test_line_map[len(a:group_state.lines)] = [a:test.file, a:test.id]
endfunction

function! s:RenderNamespace(prefix, namespace, group_state) abort
  call add(a:group_state.lines, a:prefix.." ".a:namespace.name)
  call add(a:group_state.matches, ["UltestNamespace", [len(a:group_state.lines), len(a:prefix) +1, 1]])
  let s:test_line_map[len(a:group_state.lines)] = [a:namespace.file, a:namespace.id]
endfunction

function! s:RenderFile(prefix, file, group_state) abort
  call add(a:group_state.lines, a:prefix.." ".a:file.id)
  call add(a:group_state.matches, ["UltestFile", [len(a:group_state.lines), len(a:prefix) + 1, 1]])
  let s:test_line_map[len(a:group_state.lines)] = [a:file.id, ""]
endfunction

function! s:Clear() abort
  if bufexists(s:buffer_name)
    if has("nvim-0.5.0") || has("patch-8.1.1084")
      call clearmatches(bufwinnr(s:buffer_name))
    else
      call clearmatches()
    endif
  endif
endfunction

function! s:RunCurrent() abort
  let [cur_file, cur_test] = s:GetAtLine(s:GetCurrentLine())
  if cur_file == ""
    return
  elseif cur_test == ""
    call ultest#handler#run_all(cur_file)
  else
    call ultest#handler#run_single(cur_test, cur_file)
  endif
endfunction

function! s:JumpToCurrent() abort
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

function! s:AttachToCurrent() abort
  let [cur_file, cur_test] = s:GetAtLine(s:GetCurrentLine())
  if cur_file == "" || cur_test == ""
    return
  else
    let test = get(getbufvar(cur_file, "ultest_tests", {}), cur_test)
    call ultest#output#attach(test)
  endif
endfunction

function! s:StopCurrent() abort
  let [cur_file, cur_test] = s:GetAtLine(s:GetCurrentLine())
  if cur_file == "" || cur_test == ""
    return
  else
    let test = get(getbufvar(cur_file, "ultest_tests", {}), cur_test)
    call ultest#handler#stop_test(test)
  endif
endfunction

function! s:OpenCurrentOutput() abort
  let [cur_file, cur_test] = s:GetAtLine(s:GetCurrentLine())
  if cur_file == "" || cur_test == ""
    return
  else
    let test = get(getbufvar(cur_file, "ultest_tests", {}), cur_test)
    call ultest#output#open(test)
    call ultest#output#jumpto()
  endif
endfunction

function! s:JumpToFail(direction) abort
  let index = s:GetCurrentLine() + a:direction
  let fail = {}
  while index > 0 && index < len(s:test_line_map)
    let [cur_file, cur_test] = s:test_line_map[index]
    if cur_test != ""
      let result = get(getbufvar(cur_file, "ultest_results", {}), cur_test, {})
      if get(result, "code") > 0
        call setpos(".", [0, index, 1, 0])
        return
      end
    end
    let index += a:direction
  endwhile
endfunction

function! s:GetCurrentLine() abort
  if !s:IsOpen() | return 0 | endif
  return getbufinfo(s:buffer_name)[0]["lnum"]
endfunction

function! s:GetAtLine(line) abort
  return get(s:test_line_map, a:line, ["", ""])
endfunction
