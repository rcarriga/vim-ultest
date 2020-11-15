call sign_define("test_pass", {"text":g:ultest_pass_sign, "texthl": "UltestPass"})
call sign_define("test_fail", {"text":g:ultest_fail_sign, "texthl": "UltestFail"})
call sign_define("test_running", {"text":g:ultest_running_sign, "texthl": "UltestRunning"})

function! ultest#signs#start(test) abort
    call ultest#signs#unplace(a:test)
    if s:UseVirtual()
        call s:PlaceVirtualText(a:test, g:ultest_running_text, "UltestRunning")
    else
        call s:PlaceSign(a:test, "test_running")
    endif
endfunction

function! ultest#signs#process(test) abort
    call ultest#signs#unplace(a:test)
    if s:UseVirtual()
        let text_highlight = a:test["code"] ? "UltestFail" : "UltestPass"
        let text = a:test["code"] ? g:ultest_fail_text : g:ultest_pass_text
        call s:PlaceVirtualText(a:test, text, text_highlight)
    else
        let test_icon = a:test["code"] ? "test_fail" : "test_pass"
        call s:PlaceSign(a:test, test_icon)
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
    call nvim_buf_set_virtual_text(0, namespace, str2nr(a:test["line"]) - 1, [[a:text, a:highlight]], {})
endfunction

function! ultest#signs#unplace(test)
    if s:UseVirtual()
        let namespace = s:GetNamespace(a:test)
        call nvim_buf_clear_namespace(0, namespace, 0, -1)
    else
        call sign_unplace(a:test.name, {"buffer": a:test.file})
      redraw
    endif
endfunction

function! s:GetNamespace(test)
    let virtual_namespace = "ultest".substitute(a:test["name"], " ", "_", "g")
    return nvim_create_namespace(virtual_namespace)
endfunction
