function! ultest#positions#next() abort
    if b:ultest_sorted_tests == [] | return | endif
    let current = ultest#handler#get_nearest_test(line("."), expand("%:."), v:false)
    let start = type(current) == v:t_dict ? index(b:ultest_sorted_tests, current.id) + 1 : 0
    for ind in range(start, len(b:ultest_sorted_tests) - 1)
      let test_id = b:ultest_sorted_tests[ind]
      if has_key(b:ultest_results, test_id) && b:ultest_results[test_id].code
        return s:GoToTest(b:ultest_tests[test_id])
      endif
    endfor
endfunction

function! ultest#positions#prev() abort
    if b:ultest_sorted_tests == [] | return | endif
    let current = ultest#handler#get_nearest_test(line("."), expand("%:."), v:false)
    if type(current) != v:t_dict | return | endif
    let reversed = reverse(copy(b:ultest_sorted_tests))
    let start = index(reversed, current.id)
    if current.line == line(".")
      let start += 1
    endif
    for ind in range(start, len(b:ultest_sorted_tests) - 1)
      let test_id = reversed[ind]
      if has_key(b:ultest_results, test_id) && b:ultest_results[test_id].code
        return s:GoToTest(b:ultest_tests[test_id])
      endif
    endfor
endfunction

function! s:GoToTest(test) abort
  exec "normal ".string(a:test.line)."G"
endfunction
