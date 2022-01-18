function! ultest#signs#move(tests) abort
  for test in a:tests
    if (test.type != "test") | continue | endif
    let result = get(getbufvar(test.file, "ultest_results"), test.id, {})
    if result != {}
      call ultest#signs#process([result])
    else
      call ultest#signs#start([test])
    endif
  endfor
endfunction

function! ultest#signs#start(tests) abort
  for test in a:tests
    if (test.type != "test") | continue | endif
    call ultest#signs#unplace([test])
    if !test.running | continue | endif
    if s:UseVirtual()
      call s:PlaceVirtualText(test, g:ultest_running_text, "UltestRunning")
    else
      call s:PlaceSign(test, "test_running")
    endif
  endfor
endfunction

function! ultest#signs#process(results) abort
  for result in a:results
    let test = getbufvar(result.file, "ultest_tests")[result.id]
    if (test.type != "test") | continue | endif
    call ultest#signs#unplace([test])
    if s:UseVirtual()
        let text_highlight = result.code ? "UltestFail" : "UltestPass"
        let text = result.code ? g:ultest_fail_text : g:ultest_pass_text
        call s:PlaceVirtualText(test, text, text_highlight)
    else
        let test_icon = result.code ? "test_fail" : "test_pass"
        call s:PlaceSign(test, test_icon)
    endif
  endfor
endfunction

function! s:UseVirtual() abort
    return get(g:, "ultest_virtual_text", 1) && exists("*nvim_buf_set_virtual_text")
endfunction

function! s:PlaceSign(test, test_icon) abort
    call sign_place(0, a:test.id, a:test_icon, a:test.file, {"lnum": a:test.line, "priority": 1000})
    redraw
endfunction

function! s:PlaceVirtualText(test, text, highlight) abort
    let namespace = s:GetNamespace(a:test)
    let buffer =  nvim_win_get_buf(win_getid(bufwinnr(a:test.file)))
    call nvim_buf_set_virtual_text(buffer, namespace, str2nr(a:test.line) - 1, [[a:text, a:highlight]], {})
endfunction

function! ultest#signs#unplace(tests)
  for test in a:tests
    if (test.type != "test") | continue | endif
    if s:UseVirtual()
        let namespace = s:GetNamespace(test)
        call nvim_buf_clear_namespace(0, namespace, 0, -1)
    else
        call sign_unplace(test.id, {"buffer": test.file})
      redraw
    endif
  endfor
endfunction

function! s:GetNamespace(test)
    let virtual_namespace = "ultest".substitute(a:test.id, " ", "_", "g")
    return nvim_create_namespace(virtual_namespace)
endfunction
