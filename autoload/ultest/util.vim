function ultest#util#goToBuffer(expr) abort
  let window = bufwinnr(bufnr(a:expr))
  if window == -1 | return 0 | endif

  if window != winnr()
      exe window . "wincmd w"
  endif

  return 1
endfunction
