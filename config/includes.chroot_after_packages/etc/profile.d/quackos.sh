# QuackOS shell defaults (sourced by login shells; interactive bash also via /etc/bash.bashrc.d if present)
[ -n "$BASH_VERSION" ] || return 0
case $- in *i*) ;; *) return 0 ;; esac

alias ll='ls -lah --color=auto'
alias la='ls -A --color=auto'
alias ..='cd ..'
alias grep='grep --color=auto'
alias update='quack update'

# 🦆 prompt: green when the last command succeeded, red when it did not
__quack_prompt() {
    local code=$?
    local c=32
    [ "$code" -eq 0 ] || c=31
    PS1="\[\e[${c}m\]🦆\[\e[0m\] \[\e[38;5;105m\]\u@\h\[\e[0m\]:\[\e[38;5;75m\]\w\[\e[0m\]\$ "
}
PROMPT_COMMAND=__quack_prompt
