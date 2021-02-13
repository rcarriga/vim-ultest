

function ultest#adapter#run_test(test) abort
  call ultest#process#pre(a:test)
  let runner = test#determine_runner(a:test.file)
  let base_args = test#base#build_position(runner, "nearest", a:test)
  let args = extend(base_args, [shellescape(a:test.file), a:test.id])
  let opts = test#base#options(runner, args, "nearest")
  call test#execute(runner, opts, "ultest")
endfunction

function ultest#adapter#get_patterns(file_name) abort
  let runner = test#determine_runner(a:file_name)
  if type(runner) == v:t_number | return {} | endif
  let file_type = split(runner, "#")[0]
  try
    return eval("g:test#".file_type."#patterns")
  catch /.*/
  endtry
endfunction
