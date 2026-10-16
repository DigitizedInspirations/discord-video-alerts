# Μοναδική αρχικοποίηση κενού production state — 2026-10-16

Κατάσταση: τοπική υλοποίηση/έλεγχος· production αρχικοποίηση δεν έχει εκτελεστεί.
Εγκρίθηκε ΜΙΑ αρχικοποίηση μόνο αν απουσιάζει πλήρως η `notification-state`.
Ο canary έχει ολοκληρωθεί και η disposable branch διατηρείται χωρίς νέες writes.

Μόνο manual `initialize-state.yml`, ποτέ `operate.yml`. Repository:
`DigitizedInspirations/discord-video-alerts`, trusted `main`, branch:
`notification-state`, operation: `initialize_empty_state`, confirmation:
`INITIALIZE_EMPTY_NOTIFICATION_STATE_ONCE`, expected_sha: ακριβές ελεγμένο commit.
Δεν λαμβάνει Discord/YouTube secrets και δεν εκτελεί monitoring ή ανακοινώσεις.

Αν branch/state υπάρχει ή είναι απροσπέλαστη, η ροή αρνείται χωρίς overwrite/repair.
Δημιουργεί μόνο state.json σε ανεξάρτητο root commit χωρίς parents και δημοσιεύει
τη νέα branch ατομικά στο τέλος. Κενά sources/records, νέο UUID4 και checksum.
Δεν αντιγράφει canary, παλιές δημοσιεύσεις, baselines, ουρές ή ιστορικό.
Νέο read-only GitHubStore επαληθεύει ανεξάρτητα schema/checksum/ταυτότητα/commit/tree.

MASTER/media OFF, schedule disabled. Μετά την επιτυχία δεν εκτελείς νέο run ή rerun.
Αν υπάρχει αστοχία ή αβέβαιο write, σταματάς για manual review· μόνο read-only
διάγνωση, όχι αυτόματη επανάληψη ή αποκατάσταση. Γνωστά SHAs/branch status
καταγράφονται χωρίς credentials. Baseline, backfill, Discord/webhook, YouTube key,
monitoring, recovery, cleanup και activation δεν εγκρίθηκαν. Μετά την επαλήθευση
η εργασία σταματά. Κάθε επόμενο scope απαιτεί νέα ρητή έγκριση.
[Τεχνικό σχέδιο](PRODUCTION_INITIALIZATION.md).
