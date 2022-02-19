augroup UltestOutputClose
  autocmd!
  autocmd User UltestOutputOpen  call ultest#output#close(v:false)
augroup END

augroup UltestOutputMappings
  autocmd!
  autocmd FileType UltestOutput tnoremap <buffer> q <C-\><C-N><C-W><C-P>
  autocmd FileType UltestOutput nnoremap <buffer> q <C-W><C-P>
augroup END

function! ultest#output#open(test) abort
  if type(a:test) != v:t_dict || empty(a:test) | return | endif
  doautocmd User UltestOutputOpen
  let result = get(getbufvar(a:test.file, "ultest_results", {}), a:test.id, {})
  let output = get(result, "output", "")
  if output == "" | return | endif
  let [width, height] = s:CalculateBounds(output)
  if has("nvim")
    let cmd = output
    call s:NvimOpenFloat(cmd, width, height, "UltestOutput")
    autocmd InsertEnter,CursorMoved * ++once  call ultest#output#close(v:false)
  else
    let cmd = ['less', "-R", "-Ps", output]
    call s:VimOpenFloat(cmd, width, height)
  endif
endfunction

function! ultest#output#attach(test) abort
  if type(a:test) != v:t_dict || empty(a:test) | return | endif
  let process_ids = [a:test.id, a:test.file] + a:test.namespaces
  for process_id in process_ids
    let attach_res = ultest#handler#get_attach_script(process_id)
    if type(attach_res) == v:t_list
      break
    endif
  endfor
  if type(attach_res) != v:t_list | return | endif
  let [stdout_path, py_script] = attach_res
  doautocmd User UltestOutputOpen
  let cmd = ['python3', py_script]
  let [_width, height] = s:CalculateBounds(stdout_path)
  let width = g:ultest_attach_width
  let width = width ? width : _width
  if has("nvim")
    call s:NvimOpenFloat(cmd, width, height, "UltestAttach")
    call nvim_set_current_win(g:ultest#output_windows[0])
    au TermClose * ++once call ultest#output#close(v:true)
    au InsertEnter,CursorMoved * ++once  call ultest#output#close(v:false)
  else
    call s:VimOpenFloat(cmd, width, height)
  endif
endfunction

function! ultest#output#close(force) abort
  if !s:OutputIsOpen() || !has("nvim")
    return
  endif
  if !a:force && nvim_get_current_win() == g:ultest#output_windows[0]
    autocmd InsertEnter,CursorMoved * ++once call ultest#output#close(v:false)
    return
  endif
  for window in g:ultest#output_windows
    try
      exec "bd! ".nvim_win_get_buf(window)
    catch /.*/
    endtry
  endfor
  let g:ultest#output_windows = []
endfunction

function! s:OutputIsOpen()
  return !empty(get(g:, "ultest#output_windows", []))
endfunction

function ultest#output#jumpto() abort
  if !s:OutputIsOpen()
    call ultest#output#open(ultest#handler#get_nearest_test(line("."), expand("%:."), v:false))
    if !s:OutputIsOpen()
      return
    endif
  endif
  if has("nvim")
    call nvim_set_current_win(g:ultest#output_windows[0])
  endif
endfunction

function! s:CalculateBounds(path) abort
  let width = str2nr(split(system("sed 's/\x1b\[[0-9;]*m//g' ".shellescape(a:path)." | wc -L"))[0])
  let height = str2nr(split(system("wc -l ".shellescape(a:path)))[0])

  let height = min([max([height, g:ultest_output_min_height]), g:ultest_output_max_height ? g:ultest_output_max_height : &lines])
  let width =  min([max([width, g:ultest_output_min_width]), g:ultest_output_max_width ? g:ultest_output_max_width : &columns])
  return [width, height]
endfunction

function! s:VimOpenFloat(cmd, width, height) abort
  " TODO: Background shows as solid when highlight has bg=NONE
  " See: https://github.com/vim/vim/issues/2361
  let popup_options =  {
    \ "highlight": "Normal",
    \ "border": [1,1,1,1],
    \ "maxheight": a:height,
    \ "maxwidth": a:width,
    \ "minheight": a:height,
    \ "minwidth": a:width,
    \ "borderhighlight": ["UltestBorder"],
    \ "borderchars": ['─', '│', '─', '│', '╭', '╮', '╯', '╰'],
    \ "mapping": 1
    \}
  let buf = term_start(a:cmd, {"hidden": 1, "term_kill": "term", "term_finish": 'close', "term_highlight": "Normal"})
  let g:ultest#output_windows = [popup_atcursor(buf, popup_options)]
endfunction

function! s:NvimOpenFloat(cmd, width, height, filetype) abort

  let lineNo = screenrow()
  let colNo = screencol()
  let vert_anchor = "N"
  let hor_anchor = "W"

  let row = min([1, &lines - (lineNo + a:height)])
  let col = min([1, &columns - (colNo + a:width)])

  let content_opts = {
        \ 'relative': 'cursor',
        \ 'row': row,
        \ 'col': col,
        \ 'anchor': vert_anchor.hor_anchor,
        \ 'width': a:width,
        \ 'height': a:height,
        \ 'style': 'minimal',
        \ 'border': 'rounded'
        \ }

  let out_buffer = nvim_create_buf(v:false, v:true)
  call nvim_buf_set_option(out_buffer, "filetype", a:filetype)
  let user_window = nvim_get_current_win()
  let output_window = nvim_open_win(out_buffer, v:true, content_opts)
  if type(a:cmd) == v:t_list
   call termopen(join(a:cmd, " "))
  else
    exec 'lua vim.api.nvim_chan_send(vim.api.nvim_open_term(0, {}),(io.open("'.a:cmd.'", "r"):read("*a"):gsub("\n", "\r\n")))'
  endif
  call nvim_set_current_win(user_window)
  call nvim_win_set_option(output_window, "winhl", "Normal:Normal,FloatBorder:UltestBorder")

  let g:ultest#output_windows = [output_window]
endfunction
