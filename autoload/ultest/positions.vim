augroup TestStatusPositionUpdater
    au!
    au InsertLeave,BufWrite,BufEnter * call ultest#handler#clear_old(expand("%"))
augroup END

function! ultest#positions#process(test) abort
    let b:test_status_error_positions = get(b:, "test_status_error_positions", [])
    if a:test["code"]
        call add(b:test_status_error_positions, a:test["name"])
    endif
endfunction

function! ultest#positions#clear(test) abort
    for index in range(len(get(b:, "test_status_error_positions", [])))
        if get(b:test_status_error_positions, index, "") == a:test["name"]
            call remove(b:test_status_error_positions, index)
            break
        endif
    endfor
endfunction

function! ultest#positions#next() abort
    let tests = ultest#handler#get_positions(expand("%"))
    let cur_line = line(".")
    let next_test = {"line": 0}
    for test_name in get(b:, "test_status_error_positions", [])
        let test = get(tests, test_name, {})
        if !empty(test)
            let dist = test["line"] - cur_line
            let prev_dist = next_test["line"] - cur_line
            if dist > 0 && (prev_dist < 0 || dist < prev_dist)
                let next_test = test
            endif
        endif
    endfor
    if next_test["line"]
        exec "normal ".string(next_test["line"])."G"
    endif
endfunction

function! ultest#positions#prev() abort
    let tests = ultest#handler#get_positions(expand("%"))
    let cur_line = line(".")
    let next_test = {"line": line("$") + 1}
    for test_name in get(b:, "test_status_error_positions", [])
        let test = get(tests, test_name, {})
        if !empty(test)
            let dist = cur_line - test["line"]
            let prev_dist = cur_line - next_test["line"]
            if dist > 0 && (prev_dist < 0 || dist < prev_dist)
                let next_test = test
            endif
        endif
    endfor
    if next_test["line"] <= line("$")
        exec "normal ".string(next_test["line"])."G"
    endif
endfunction

function! ultest#positions#nearest(file, line) abort
    let position = {"file": a:file,"line": a:line, "col":1}
    let patterns = s:GetTestPatterns()
    if empty(patterns) | return {} | endif
    let nearest = test#base#nearest_test(position, patterns)
    let nearest_test = get(get(nearest, "test"), 0)
    if type(nearest_test) == v:t_string
        let position["name"] = nearest_test
        let position["line"] = get(nearest, "test_line")
        return position
    endif
    return {}
endfunction

function! s:GetTestPatterns() abort
    let patterns = get(g:, "test#".&filetype."#patterns", {})
    if empty(patterns)
        " In case file hasn't been loaded yet.
        try | call call("test#".&filetype."#bad_function", []) | catch /Unknown/ | endtry
        let patterns = get(g:, "test#".&filetype."#patterns", {})
    endif
    return patterns
endfunction

function! s:find_match(line, patterns) abort
  let matches = map(copy(a:patterns), 'matchlist(a:line, v:val)')
  return get(filter(matches, '!empty(v:val)'), 0, [])
endfunction
