augroup UltestOutputClose
  autocmd!
  autocmd InsertEnter,CursorMoved *  call ultest#output#close(v:false)
  autocmd User UltestOutputOpen  call ultest#output#close(v:false)
augroup END

augroup UltestOutputMappings
  autocmd!
  autocmd FileType UltestOutput tnoremap <buffer> q <C-\><C-N><C-W><C-K>
  autocmd FileType UltestOutput nnoremap <buffer> q <C-W><C-K>
augroup END

function! ultest#output#open(test) abort
  if type(a:test) != v:t_dict || empty(a:test) | return | endif
  doautocmd User UltestOutputOpen
  let result = get(getbufvar(a:test.file, "ultest_results", {}), a:test.id, {})
  if get(result, "code") == 0 | return | endif
  let output = get(result, "output", "")
  let [width, height] = s:CalculateBounds(output)
  let cmd = ['less', "-R", "-Ps", output]
  if has("nvim")
    call s:NvimOpenFloat(cmd, width, height, "UltestOutput")
  else
    call s:VimOpenFloat(cmd, width, height)
    exec "tnoremap <buffer><silent> q <C-W>N:call popup_close(".winid.")<CR>"
  endif
endfunction

function! ultest#output#attach(test) abort
  if type(a:test) != v:t_dict || empty(a:test) | return | endif
  let attach_res = ultest#handler#get_attach_script(a:test.id)
  if type(attach_res) != v:t_list | return | endif
  let [stdout_path, py_script] = attach_res
  doautocmd User UltestOutputOpen
  let cmd = ['python', py_script]
  let [width, height] = s:CalculateBounds(stdout_path)
  if has("nvim")
    call s:NvimOpenFloat(cmd, width, height, "UltestAttach")
    call nvim_set_current_win(g:ultest#output_windows[0])
    au TermClose * ++once call ultest#output#close(v:true)
  else
    call s:VimOpenFloat(cmd, width, height)
  endif
endfunction

function! ultest#output#close(force) abort
  if !s:OutputIsOpen()
    return
  endif
  if !a:force && nvim_get_current_win() == g:ultest#output_windows[0]
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
    call ultest#output#open(ultest#handler#get_nearest_test(line("."), expand("%"), v:false))
    if !s:OutputIsOpen()
      return
    endif
  endif
  if has("nvim")
    call nvim_set_current_win(g:ultest#output_windows[0])
  endif
endfunction

function! s:CalculateBounds(path) abort
  let width = str2nr(split(system("sed 's/\x1b\[[0-9;]*m//g' ".a:path." | wc -L"))[0]) + 1
  let height = str2nr(split(system("wc -l ".a:path))[0])

  let height = max([min([height, &lines/2]), 20])
  let width =  max([min([width, &columns/2]), 40])
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
  let winid = popup_atcursor(buf, popup_options)
endfunction

function! s:NvimOpenFloat(cmd, width, height, filetype) abort

  let lineNo = screenrow()
  let colNo = screencol()
  let vert_anchor = lineNo + a:height < &lines - 3 ? "N" : "S"
  let hor_anchor = colNo + a:width < &columns + 3 ? "W" : "E"


  let opts = {
        \ 'relative': 'cursor',
        \ 'row': vert_anchor == "N" ? 2 : -1,
        \ 'col': hor_anchor == "W" ? 3 : -2,
        \ 'anchor': vert_anchor.hor_anchor,
        \ 'width': a:width,
        \ 'height': a:height,
        \ 'style': 'minimal'
        \ }

  let out_buffer = nvim_create_buf(v:false, v:true)
  let user_window = nvim_get_current_win()
  let output_window = nvim_open_win(out_buffer, v:true, opts)
  call termopen(join(a:cmd, " "))
  exec "setfiletype ".a:filetype
  call nvim_set_current_win(user_window)
  let output_win_id = nvim_win_get_number(output_window)
  call setwinvar(output_win_id, "&winhl", "Normal:Normal")

  let opts.row += vert_anchor == "N" ? -1 : 1
  let opts.height += 2
  let opts.col += hor_anchor == "W" ? -2 : 2
  let opts.width += 3

  let top = "╭" . repeat("─", a:width+1) . "╮"
  let mid = "│" . repeat(" ", a:width+1) . "│"
  let bot = "╰" . repeat("─", a:width+1) . "╯"
  let lines = [top] + repeat([mid], a:height) + [bot]
  let s:buf = nvim_create_buf(v:false, v:true)
  call nvim_buf_set_lines(s:buf, 0, -1, v:true, lines)
  let border_window = nvim_open_win(s:buf, v:false, opts)
  let border_win_id = nvim_win_get_number(border_window)
  call setwinvar(border_win_id, "&winhl", "Normal:Normal")
  call matchadd("UltestBorder", ".*",100, -1, {"window": border_window})
  let g:ultest#output_windows = [output_window, border_window]
endfunction
