augroup UltestOutputClose
  autocmd!
  autocmd InsertEnter,CursorMoved *  call ultest#output#close()
  autocmd User UltestOutputOpen  call ultest#output#close()
augroup END

function! ultest#output#open(output) abort
  if empty(a:output) | return | endif
  doautocmd User UltestOutputOpen
  call s:OpenFloat(a:output)
endfunction

function! ultest#output#close() abort
  if !s:OutputIsOpen()
    return
  endif
  if nvim_get_current_win() == g:ultest#output_windows[0]
    return
  endif
  for window in g:ultest#output_windows
    call s:CloseFloat(window)
  endfor
  let g:ultest#output_windows = []
endfunction
function! s:OutputIsOpen()

  return !empty(get(g:, "ultest#output_windows", []))
endfunction

function ultest#output#jumpto() abort
  if !s:OutputIsOpen()
    call ultest#output#open(ultest#handler#nearest_output(expand("%"), v:false))
    if !s:OutputIsOpen()
      return
    endif
  endif
  call nvim_set_current_win(g:ultest#output_windows[0])
endfunction

function! s:OpenFloat(path) abort
  let width = str2nr(split(system("sed 's/\x1b\[[0-9;]*m//g' ".a:path." | wc -L"))[0])
  let height = str2nr(split(system("wc -l ".a:path))[0])

  let height = min([height, &lines/2])
  let width =  min([width, &columns/2])

  let lineNo = screenrow()
  let colNo = screencol()
  let vert_anchor = lineNo + height < &lines - 3 ? "N" : "S"
  let hor_anchor = colNo + width < &columns + 3 ? "W" : "E"


  let opts = {
        \ 'relative': 'cursor',
        \ 'row': vert_anchor == "N" ? 2 : -1,
        \ 'col': hor_anchor == "W" ? 3 : -2,
        \ 'anchor': vert_anchor.hor_anchor,
        \ 'width': width,
        \ 'height': height,
        \ 'style': 'minimal'
        \ }

  let out_buffer = nvim_create_buf(v:false, v:true)
  let user_window = nvim_get_current_win()
  let output_window = nvim_open_win(out_buffer, v:true, opts)
  call termopen('less -R -Ps '.a:path)
  call nvim_set_current_win(user_window)
  let output_win_id = nvim_win_get_number(output_window)
  call setwinvar(output_win_id, "&winhl", "Normal:Normal")

  let opts.row += vert_anchor == "N" ? -1 : 1
  let opts.height += 2
  let opts.col += hor_anchor == "W" ? -2 : 2
  let opts.width += 3

  let top = "╭" . repeat("─", width+1) . "╮"
  let mid = "│" . repeat(" ", width+1) . "│"
  let bot = "╰" . repeat("─", width+1) . "╯"
  let lines = [top] + repeat([mid], height) + [bot]
  let s:buf = nvim_create_buf(v:false, v:true)
  call nvim_buf_set_lines(s:buf, 0, -1, v:true, lines)
  let border_window = nvim_open_win(s:buf, v:false, opts)
  let border_win_id = nvim_win_get_number(border_window)
  call setwinvar(border_win_id, "&winhl", "Normal:Normal")
  call matchadd("UltestBorder", ".*",100, -1, {"window": border_window})
  let g:ultest#output_windows = [output_window, border_window]
endfunction

function! s:CloseFloat(window)
  try
    let output_buffer = nvim_win_get_buf(a:window)
    exec "bd! ".output_buffer
    call nvim_win_close(a:window, v:true)
  catch /Invalid/
  endtry
endfunction
