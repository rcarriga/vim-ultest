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

function! s:UpdateBufferTests(tests) abort
  let new_tests = {}
  for test in a:tests
    if index(g:ultest_buffers, test.file) == -1
      let g:ultest_buffers = add(g:ultest_buffers, test.file)
    endif
    if !has_key(new_tests, test.file)
      let new_tests[test.file] = {}
    endif
    let new_tests[test.file][test.id] = test
  endfor
  for [file, new_file_tests] in items(new_tests)
    let tests = getbufvar(file, "ultest_tests", {})
    call extend(tests, new_file_tests)
  endfor
endfunction

function! s:UpdateBufferResults(results) abort
  let new_results = {}
  for result in a:results
    if !has_key(new_results, result.file)
      let new_results[result.file] = {}
    endif
    let new_results[result.file][result.id] = result
  endfor
  for [file, new_file_results] in items(new_results)
    let tests = getbufvar(file, "ultest_results", {})
    call extend(tests, new_file_results)
  endfor
endfunction

function! s:ClearTests(tests) abort
  for test in a:tests
    let buf_tests = getbufvar(test.file, "ultest_tests")
    if has_key(buf_tests, test.id)
      call remove(buf_tests, test.id)
    endif
  endfor
endfunction

function! s:ClearTestResults(tests) abort
  for test in a:tests
    let results = getbufvar(test.file, "ultest_results")
    if has_key(results, test.id)
      call remove(results, test.id)
    endif
  endfor
endfunction

function! s:SeparateTestAndResults(combined) abort
  let tests = []
  let results = []
  for [test, result] in a:combined
    call add(tests, test)
    call add(results, result)
  endfor
  return [tests, results]
endfunction

function ultest#process#new(tests) abort
  call ultest#process#pre(a:tests)
  call s:UpdateBufferTests(a:tests)
  call s:CallProcessor("new", [a:tests])
endfunction

function ultest#process#start(tests) abort
  call ultest#process#pre(a:tests)
  call s:UpdateBufferTests(a:tests)
  call s:ClearTestResults(a:tests)
  call s:CallProcessor("start", [a:tests])
endfunction

function ultest#process#move(tests) abort
  call ultest#process#pre(a:tests)
  call s:UpdateBufferTests(a:tests)
  call s:CallProcessor("move", [a:tests])
endfunction

function ultest#process#replace(combined) abort
  let [tests, results] = s:SeparateTestAndResults(a:combined)
  call ultest#process#pre(tests)
  call s:UpdateBufferTests(tests)
  call s:UpdateBufferResults(results)
  call s:CallProcessor("replace", [results])
endfunction

function ultest#process#clear(tests) abort
  call ultest#process#pre(a:tests)
  call s:ClearTests(a:tests)
  call s:ClearTestResults(a:tests)
  call s:CallProcessor("clear", [a:tests])
endfunction

function ultest#process#exit(combined) abort
  let [tests, results] = s:SeparateTestAndResults(a:combined)
  call ultest#process#pre(tests)
  call s:UpdateBufferTests(tests)
  call s:UpdateBufferResults(results)
  call s:CallProcessor("exit", [results])
endfunction

function ultest#process#pre(tests) abort
  for test in a:tests
    if type(test.name) == v:t_list
      if exists("*list2str")
        let newName = list2str(test.name)
      else
        let newName = join(map(test.name, {nr, val -> nr2char(val)}), '')
      endif
      let test.name = newName
    endif
  endfor
endfunction
