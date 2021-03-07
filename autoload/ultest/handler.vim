
if has("nvim")
  let s:is_nvim = v:true
else
  let s:is_nvim = v:false
  let s:yarp = yarp#py3('ultest')
endif

function! s:Call(func, args) abort
  if s:is_nvim
    return call(a:func, a:args)
  else
    let args = copy(a:args)
    call insert(args, a:func)
    return call(s:yarp.call, args, s:yarp)
  endif
endfunction

function! ultest#handler#strategy(...) abort
  call s:Call('_ultest_strategy', a:000)
endfunction

function! ultest#handler#run_all(...) abort
  call s:Call('_ultest_run_all', a:000)
endfunction

function! ultest#handler#run_nearest(...) abort
  call s:Call('_ultest_run_nearest', a:000)
endfunction

function! ultest#handler#run_single(...) abort
  call s:Call('_ultest_run_single', a:000)
endfunction

function! ultest#handler#update_positions(...) abort
  call s:Call('_ultest_update_positions', a:000)
endfunction

function! ultest#handler#get_sorted_ids(...) abort
  return s:Call('_ultest_get_sorted_test_ids', a:000)
endfunction

function! ultest#handler#get_nearest_test(...) abort
  return s:Call('_ultest_get_nearest_test', a:000)
endfunction

function! ultest#handler#get_attach_script(...) abort
  return s:Call('_ultest_get_attach_script', a:000)
endfunction

function! ultest#handler#stop_test(...) abort
  return s:Call('_ultest_stop_test', a:000)
endfunction

function! ultest#handler#get_process(...) abort
  return s:Call('_ultest_get_process', a:000)
endfunction
