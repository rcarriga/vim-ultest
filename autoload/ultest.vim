""
" @public
" @usage [file]
" Get the status of a file. If the [file] argument is not given, the current
" buffer will be used. Full paths are expected for [file].
"
" The return value is a dict with the following keys:
"
" 'tests': Number of tests found
"
" 'passed': Number of tests passed
"
" 'failed': Number of tests failed
"
" 'running': Number of tests running
function! ultest#status(...) abort
  try
    let file = a:0 == 1 ? a:1 : expand("%:.")
    let ids = getbufvar(file, "ultest_sorted_tests", [])
    let tests = getbufvar(file, "ultest_tests", {})
    let results = getbufvar(file, "ultest_results", {})
    let status = {"tests": len(ids), "passed": 0, "failed": 0, "running": 0}
    for test_id in ids
      let result = get(results, test_id, {})
      if result != {}
        let key = result.code ? "failed" : "passed"
        let status[key] += 1
      elseif get(get(tests, test_id, {}), "running")
        let status.running += 1
      endif
    endfor
    return status
  catch /.*/
    return {"tests": 0, "passed": 0, "failed": 0, "running": 0}
  endtry

endfunction

""
" @public
" @usage [file]
" Check if a file has tests detected within it.
" N.B. This can return false if a file has not been processed yet.
" You can use the 'User UltestPositionsUpdate' autocommand to detect when a
" file has been processed.
"
"If the [file] argument is not given, the current
" buffer will be used. Full paths are expected for [file].
function! ultest#is_test_file(...) abort
    let file = a:0 == 1 ? a:1 : expand("%:.")
    return !empty(getbufvar(file, "ultest_tests", {}))
endfunction

function! ultest#run_file(...) abort
  let file = a:0 == 1 ? a:1 : expand("%:.")
  call ultest#handler#run_all(file)
endfunction

function! ultest#run_nearest(...) abort
  let file = a:0 == 1 ? a:1 : expand("%:.")
  let line = getbufinfo(file)[0]["lnum"]
  call ultest#handler#run_nearest(line, file)
endfunction

function! ultest#stop_file(...) abort
  let file = a:0 == 1 ? a:1 : expand("%:.")
  let ids = getbufvar(file, "ultest_sorted_tests", [])
  let tests = getbufvar(file, "ultest_tests", {})
  for test_id in ids
    let test = get(tests, test_id)
    call ultest#handler#stop_test(test)
  endfor
  call ultest#handler#update_positions(file)
endfunction

function! ultest#stop_nearest(...) abort
  let file = a:0 == 1 ? a:1 : expand("%:.")
  let test = ultest#handler#get_nearest_test(line("."), file, v:false)
  call ultest#handler#stop_test(test)
  call ultest#handler#update_positions(file)
endfunction
