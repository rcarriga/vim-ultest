
if has("nvim")
    let s:is_nvim = v:true
else
    let s:is_nvim = v:false
    let s:yarp = yarp#py3('ultest')
endif

function! ultest#handler#strategy(cmd) abort
    if s:is_nvim
        call _ultest_strategy(a:cmd)
    else
        call s:yarp.call('_ultest_strategy', a:cmd)
    endif
endfunction

function! ultest#handler#run_all(file_name) abort
    if s:is_nvim
        call _ultest_run_all(a:file_name)
    else
        call s:yarp.call('_ultest_run_all', a:file_name)
    endif
endfunction

function! ultest#handler#run_nearest(file_name) abort
    if s:is_nvim
        call _ultest_run_nearest(a:file_name)
    else
        call s:yarp.call('_ultest_run_nearest', a:file_name)
    endif
endfunction

function! ultest#handler#clear_old(file_name) abort
    if s:is_nvim
        call _ultest_clear_old(a:file_name)
    else
        call s:yarp.call('_ultest_clear_old', a:file_name)
    endif
endfunction

function! ultest#handler#save_positions(file_name) abort
    if s:is_nvim
        call _ultest_set_positions(a:file_name)
    else
        call s:yarp.call('_ultest_positions', a:file_name)
    endif
endfunction

function! ultest#handler#get_positions(file_name) abort
    if s:is_nvim
        return _ultest_get_positions(a:file_name)
    else
        return s:yarp.call('_ultest_get_positions', a:file_name)
    endif
endfunction

function! ultest#handler#nearest_output(file_name, strict) abort
    if s:is_nvim
        return _ultest_nearest_output(a:file_name, a:strict)
    else
        return s:yarp.call('_ultest_nearest_output', a:file_name, a:strict)
    endif
endfunction

function! ultest#handler#test_output(file_name, test_name)
    if s:is_nvim
        return _ultest_get_output(a:test_name)
    else
        call s:yarp.call('_ultest_get_output', a:test_name)
    endif
endfunction
