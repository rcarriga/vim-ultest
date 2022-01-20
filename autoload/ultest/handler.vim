
if has("nvim")
  let s:is_nvim = v:true
  let s:update_warn_sent = 0
else
  let s:is_nvim = v:false
  let s:yarp = yarp#py3('ultest')
endif

function! s:Call(func, args) abort
  if s:is_nvim
    try
      return call(a:func, a:args)
    catch /.*Unknown function.*/
      " Send twice because first one isn't shown if triggered during startup
      if s:update_warn_sent < 2 
        echom "Error: vim-ultest remote function not detected, try running :UpdateRemotePlugins on install/update"
        let s:update_warn_sent += 1
      endif
    catch
      " Send twice because first one isn't shown if triggered during startup
      if s:update_warn_sent < 2 
        echom "Error: vim-ultest encountered an unknown error on startup ".v:exception
        let s:update_warn_sent += 1
      endif
    endtry
  else
    let args = copy(a:args)
    call insert(args, a:func)
    return call(s:yarp.call, args, s:yarp)
  endif
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

function! ultest#handler#run_last(...) abort
  call s:Call('_ultest_run_last', a:000)
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

function! ultest#handler#external_start(...) abort
  return s:Call('_ultest_external_start', a:000)
endfunction

function! ultest#handler#external_result(...) abort
  return s:Call('_ultest_external_result', a:000)
endfunction

function! ultest#handler#safe_split(...) abort
  return s:Call('_ultest_safe_split', a:000)
endfunction

function! ultest#handler#clear_results(...) abort
  return s:Call('_ultest_clear_results', a:000)
endfunction
