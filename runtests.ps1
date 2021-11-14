$repeats = 40
DO {
    python tests.py
    $repeats--
    if (($repeats % 10) -eq 0) {
        echo $repeats
    }
} While ($repeats -ge 0)
