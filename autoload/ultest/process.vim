let g:ultest#active_processors = []
let g:ultest_buffers = []
for processor in g:ultest#processors
  if get(processor, "condition", 1)
    call insert(g:ultest#active_processors, processor)
  endif
endfor

function! s:CallProcessor(event, args) abort
  for processor in g:ultest#active_processors
    let func = get(processor, a:event, "")
    if func != ""
      if get(processor, "lua") 
        call luaeval(func."(unpack(_A))", a:args)
      else
        call call(func, a:args)
      endif
    endif
  endfor
endfunction

function ultest#process#new(test) abort
  call ultest#process#pre(a:test)
  if index(g:ultest_buffers, a:test.file) == -1
    let g:ultest_buffers = add(g:ultest_buffers, a:test.file)
  endif
  let tests = getbufvar(a:test.file, "ultest_tests", {})
  let tests[a:test.id] = a:test
  call s:CallProcessor("new", [a:test])
endfunction

function ultest#process#start(test) abort
  call ultest#process#pre(a:test)
  let tests = getbufvar(a:test.file, "ultest_tests", {})
  let tests[a:test.id] = a:test
  let results = getbufvar(a:test.file, "ultest_results")
  if has_key(results, a:test.id)
    call remove(results, a:test.id)
  endif
  call s:CallProcessor("start", [a:test])
endfunction

function ultest#process#move(test) abort
  call ultest#process#pre(a:test)
  let tests = getbufvar(a:test.file, "ultest_tests")
  let tests[a:test.id] = a:test
  call s:CallProcessor("move", [a:test])
endfunction

function ultest#process#replace(test, result) abort
  call ultest#process#pre(a:test)
  let tests = getbufvar(a:test.file, "ultest_tests")
  let tests[a:test.id] = a:test
  let results = getbufvar(a:result.file, "ultest_results")
  let results[a:result.id] = a:result
  call s:CallProcessor("replace", [a:result])
endfunction

function ultest#process#clear(test) abort
  call ultest#process#pre(a:test)
  let tests = getbufvar(a:test.file, "ultest_tests")
  if has_key(tests, a:test.id)
    call remove(tests, a:test.id)
  endif
  let results = getbufvar(a:test.file, "ultest_results")
  if has_key(results, a:test.id)
    call remove(results, a:test.id)
  endif
  call s:CallProcessor("clear", [a:test])
endfunction

function ultest#process#exit(test, result) abort
  call ultest#process#pre(a:test)
  if !has_key(getbufvar(a:result.file, "ultest_tests", {}), a:result.id)
    return
  endif
  let tests = getbufvar(a:test.file, "ultest_tests", {})
  let tests[a:test.id] = a:test
  let results = getbufvar(a:result.file, "ultest_results")
  let results[a:result.id] = a:result
  call s:CallProcessor("exit", [a:result])
endfunction

function ultest#process#pre(test) abort
  if type(a:test.name) == v:t_list
    if exists("*list2str")
      let newName = list2str(a:test.name)
    else
      let newName = join(map(a:test.name, {nr, val -> nr2char(val)}), '')
    endif
    let a:test.name = newName
  endif
endfunction
