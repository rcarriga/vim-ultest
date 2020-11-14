

function ultest#adapter#run_test(test) abort
  call ultest#process#pre(a:test)
  let runner = test#determine_runner(a:test.file)
  let base_args = test#base#build_position(runner, "nearest", a:test)
  let args = add(base_args, string(str2list(json_encode(a:test))))
  let opts = test#base#options(runner, args, "nearest")
  call test#execute(runner, opts, "ultest")
endfunction
