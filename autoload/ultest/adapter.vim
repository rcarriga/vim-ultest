

function ultest#adapter#run_test(test) abort
  call ultest#process#pre(a:test)

  let runner = test#determine_runner(a:test.file)
  let executable = test#base#executable(runner)

  let base_args = test#base#build_position(runner, "nearest", a:test)
  let args = test#base#options(runner, base_args)
  let args = test#base#build_args(runner, args, "ultest")

  let cmd = [executable] + args

  call filter(cmd, '!empty(v:val)')
  if has_key(g:, 'test#transformation')
    let cmd = g:test#custom_transformations[g:test#transformation](cmd)
  endif

  call ultest#handler#strategy(cmd, a:test)
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
