let g:ultest#active_processors = []
for processor in g:ultest#processors
  if get(processor, "condition", 1)
    call insert(g:ultest#active_processors, processor)
  endif
endfor

function ultest#process#start(position) abort
  call ultest#process#pre(a:position)
  for processor in g:ultest#active_processors
    let start = get(processor, "start", "")
    if start != ""
      call function(start)(a:position)
    endif
  endfor
endfunction

function ultest#process#clear(position) abort
  call ultest#process#pre(a:position)
  for processor in g:ultest#active_processors
    let clear = get(processor, "clear", "")
    if clear != ""
      call function(clear)(a:position)
    endif
  endfor
endfunction

function ultest#process#exit(result) abort
  call ultest#process#pre(a:result)
  for processor in g:ultest#active_processors
    let exit = get(processor, "exit", "")
    if exit != ""
      call function(exit)(a:result)
    endif
  endfor
endfunction

function ultest#process#pre(position) abort
  if len(get(a:position, "name", []))
    let newName = list2str(a:position.name)
    echom newName
    let a:position.name = newName
  endif
endfunction
