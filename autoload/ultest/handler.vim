
if has("nvim")
    let s:is_nvim = v:true
else
    let s:is_nvim = v:false
    let s:yarp = yarp#py3('ultest')
endif

function! s:PreRun(file_name) abort
  call setbufvar(a:file_name, "ultest_results", getbufvar(a:file_name, "ultest_results", {}))
  call setbufvar(a:file_name, "ultest_tests", getbufvar(a:file_name, "ultest_tests", {}))
  call setbufvar(a:file_name, "ultest_sorted_tests", getbufvar(a:file_name, "ultest_sorted_tests", []))
endfunction

function! ultest#handler#strategy(cmd) abort
    if s:is_nvim
        call _ultest_strategy(a:cmd)
    else
        call s:yarp.call('_ultest_strategy', a:cmd)
    endif
endfunction

function! ultest#handler#run_all(file_name) abort
    call s:PreRun(a:file_name)
    if s:is_nvim
        call _ultest_run_all(a:file_name)
    else
        call s:yarp.call('_ultest_run_all', a:file_name)
    endif
endfunction

function! ultest#handler#run_nearest(line, file_name) abort
    call s:PreRun(a:file_name)
    if s:is_nvim
        call _ultest_run_nearest(a:line, a:file_name)
    else
        call s:yarp.call('_ultest_run_nearest', a:line, a:file_name)
    endif
endfunction

function! ultest#handler#run_single(test_id, file_name) abort
    call s:PreRun(a:file_name)
    if s:is_nvim
        call _ultest_run_single(a:test_id, a:file_name)
    else
        call s:yarp.call('_ultest_run_single', a:test_id, a:file_name)
    endif
endfunction

function! ultest#handler#update_positions(file_name) abort
    call s:PreRun(a:file_name)
    if s:is_nvim
        call _ultest_update_positions(a:file_name)
    else
        call s:yarp.call('_ultest_update_positions', a:file_name)
    endif
endfunction

function! ultest#handler#get_sorted_ids(file_name) abort
    if s:is_nvim
        return _ultest_get_sorted_test_ids(a:file_name)
    else
        return s:yarp.call('_ultest_get_sorted_test_ids', a:file_name)
    endif
endfunction

function! ultest#handler#get_nearest_test(line, file_name, strict) abort
    if s:is_nvim
        return _ultest_get_nearest_test(a:line, a:file_name, a:strict)
    else
        return s:yarp.call('_ultest_get_nearest_test', a:line, a:file_name, a:strict)
    endif
endfunction

function! ultest#handler#get_attach_script(test) abort
    if s:is_nvim
        return _ultest_get_attach_script(a:test)
    else
        return s:yarp.call('_ultest_get_attach_script', a:test)
    endif
endfunction

function! ultest#handler#clear_test(test_id) abort
    if s:is_nvim
        return _ultest_clear_test(a:test_id)
    else
        return s:yarp.call('_ultest_clear_test', a:test)
    endif
endfunction
