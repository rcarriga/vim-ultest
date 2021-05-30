
function! ultest#adapter#get_runner(file)
  if exists('g:test#project_root')
    let cwd = getcwd()
    execute 'cd' g:test#project_root
  endif
  let runner = test#determine_runner(a:file)
  if exists('g:test#project_root')
    exec 'cd'.cwd
  endif
  return runner
endfunction

function! ultest#adapter#build_cmd(test, scope) abort
  if exists('g:test#project_root')
    let cwd = getcwd()
    execute 'cd' g:test#project_root
  endif
  let a:test.file = fnamemodify(a:test.file, get(g:, "test#filename_modifier", ":."))
  call ultest#process#pre(a:test)
  let runner = test#determine_runner(a:test.file)
  let executable = test#base#executable(runner)

  let base_args = test#base#build_position(runner, a:scope, a:test)
  let args = test#base#options(runner, base_args)
  let args = test#base#build_args(runner, args, "ultest")

  let cmd = split(executable) + args

  call filter(cmd, '!empty(v:val)')
  if has_key(g:, 'test#transformation')
    let cmd = g:test#custom_transformations[g:test#transformation](cmd)
  endif
  for index in range(len(cmd))
    if cmd[index] == a:test.file
      let cmd[index] = shellescape(a:test.file)
    end
  endfor
  let cmd = ultest#handler#safe_split(cmd)
  if exists('g:test#project_root')
    exec 'cd'.cwd
  endif
  return cmd
endfunction

function ultest#adapter#run_test(test) abort
  let cmd = ultest#adapter#build_cmd(a:test)
  call ultest#handler#strategy(cmd, a:test)
endfunction

function ultest#adapter#get_patterns(file_name) abort
  let runner = test#determine_runner(a:file_name)
  if type(runner) == v:t_number | return {} | endif
  let file_type = split(runner, "#")[0]
  let ultest_pattern = get(g:ultest_patterns, runner, get(g:ultest_patterns, file_type))
  if type(ultest_pattern) == v:t_dict
    return ultest_pattern
  endif
  try
    try
      return eval("g:test#".runner."#patterns")
    catch /.*/
      return eval("g:test#".file_type."#patterns")
    endtry
  catch /.*/
  endtry
endfunction
