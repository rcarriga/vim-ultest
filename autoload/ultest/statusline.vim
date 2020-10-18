function! ultest#statusline#process(test) abort
    call setbufvar(a:test["file"], "ultest_total", get(b:, "ultest_total", 0) + 1)
    if a:test["code"]
        call setbufvar(a:test["file"], "ultest_failed", get(b:, "ultest_failed", 0) + 1)
    else
        call setbufvar(a:test["file"], "ultest_passed", get(b:, "ultest_passed", 0) + 1)
    endif
endfunction

function! ultest#statusline#remove(test) abort
    call setbufvar(a:test["file"], "ultest_total", get(b:, "ultest_total", 1) - 1)
    if a:test["code"]
        call setbufvar(a:test["file"], "ultest_failed", get(b:, "ultest_failed", 1) - 1)
    else
        call setbufvar(a:test["file"], "ultest_passed", get(b:, "ultest_passed", 1) - 1)
    endif
endfunction
