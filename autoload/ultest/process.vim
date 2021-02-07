let g:ultest#active_processors = []
let g:ultest_buffers = []
for processor in g:ultest#processors
  if get(processor, "condition", 1)
    call insert(g:ultest#active_processors, processor)
  endif
endfor

function ultest#process#store_sorted_ids(file, ids) abort
  call setbufvar(a:file, "ultest_sorted_tests", a:ids)
endfunction

function ultest#process#new(test) abort
  call ultest#process#pre(a:test)
  if index(g:ultest_buffers, a:test.file) == -1
    let g:ultest_buffers = add(g:ultest_buffers, a:test.file)
  endif
  let tests = getbufvar(a:test.file, "ultest_tests", {})
  let tests[a:test.id] = a:test
  for processor in g:ultest#active_processors
    let new = get(processor, "new", "")
    if new != ""
      call function(new)(a:test)
    endif
  endfor
endfunction

function ultest#process#start(test) abort
  call ultest#process#pre(a:test)
  let tests = getbufvar(a:test.file, "ultest_tests", {})
  let tests[a:test.id] = a:test
  let results = getbufvar(a:test.file, "ultest_results")
  if has_key(results, a:test.id)
    call remove(results, a:test.id)
  endif
  for processor in g:ultest#active_processors
    let start = get(processor, "start", "")
    if start != ""
      call function(start)(a:test)
    endif
  endfor
endfunction

function ultest#process#move(test) abort
  call ultest#process#pre(a:test)
  let tests = getbufvar(a:test.file, "ultest_tests")
  let tests[a:test.id] = a:test
  for processor in g:ultest#active_processors
    let start = get(processor, "move", "")
    if start != ""
      call function(start)(a:test)
    endif
  endfor
endfunction

function ultest#process#replace(test, result) abort
  call ultest#process#pre(a:test)
  let tests = getbufvar(a:test.file, "ultest_tests")
  let tests[a:test.id] = a:test
  let results = getbufvar(a:result.file, "ultest_results")
  let results[a:result.id] = a:result
  for processor in g:ultest#active_processors
    let exit = get(processor, "replace", "")
    if exit != ""
      call function(exit)(a:result)
    endif
  endfor
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
  for processor in g:ultest#active_processors
    let clear = get(processor, "clear", "")
    if clear != ""
      call function(clear)(a:test)
    endif
  endfor
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
  for processor in g:ultest#active_processors
    let exit = get(processor, "exit", "")
    if exit != ""
      call function(exit)(a:result)
    endif
  endfor
endfunction

function ultest#process#pre(test) abort
  if len(get(a:test, "name", []))
    let newName = list2str(a:test.name)
    let a:test.name = newName
  endif
endfunction
