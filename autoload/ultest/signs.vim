function! ultest#signs#move(test) abort
  let result = get(getbufvar(a:test.file, "ultest_results"), a:test.id, {})
  if result != {}
    call ultest#signs#process(result)
  else
    call ultest#signs#start(a:test)
  endif
endfunction

function! ultest#signs#start(test) abort
    call ultest#signs#unplace(a:test)
    if !a:test.running | return | endif
    if s:UseVirtual()
        call s:PlaceVirtualText(a:test, g:ultest_running_text, "UltestRunning")
    else
        call s:PlaceSign(a:test, "test_running")
    endif
endfunction

function! ultest#signs#process(result) abort
    let test = getbufvar(a:result.file, "ultest_tests")[a:result.id]
    call ultest#signs#unplace(test)
    if s:UseVirtual()
        let text_highlight = a:result.code ? "UltestFail" : "UltestPass"
        let text = result.code ? g:ultest_fail_text : g:ultest_pass_text
        call s:PlaceVirtualText(test, text, text_highlight)
    else
        let test_icon = a:result.code ? "test_fail" : "test_pass"
        call s:PlaceSign(test, test_icon)
    endif
endfunction

function! s:UseVirtual() abort
    return get(g:, "ultest_virtual_text", 1) && exists("*nvim_buf_set_virtual_text")
endfunction

function! s:PlaceSign(test, test_icon) abort
    call sign_place(0, a:test.name, a:test_icon, a:test.file, {"lnum": a:test.line, "priority": 1000})
    redraw
endfunction

function! s:PlaceVirtualText(test, text, highlight) abort
    let namespace = s:GetNamespace(a:test)
    let buffer =  nvim_win_get_buf(win_getid(bufwinnr(a:test.file)))
    call nvim_buf_set_virtual_text(buffer, namespace, str2nr(a:test.line) - 1, [[a:text, a:highlight]], {})
endfunction

function! ultest#signs#unplace(test)
    if s:UseVirtual()
        let namespace = s:GetNamespace(a:test)
        call nvim_buf_clear_namespace(0, namespace, 0, -1)
    else
        call sign_unplace(a:test["name"], {"buffer": a:test.file})
      redraw
    endif
endfunction

function! s:GetNamespace(test)
    let virtual_namespace = "ultest".substitute(a:test.name, " ", "_", "g")
    return nvim_create_namespace(virtual_namespace)
endfunction
