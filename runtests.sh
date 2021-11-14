repeats=40

while [ $repeats -ge 0 ]; do
    python tests.py >> results.txt
    repeats=$((repeats-1))
    if [[ $((repeats%10)) -eq 0 ]]
    then
        echo "$repeats iterations left"
    fi
done