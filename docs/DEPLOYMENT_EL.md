# Ελεγχόμενη εγκατάσταση — API cloud αποτέλεσμα 2026-10-16

Το εγκεκριμένο audited push f25153002b4dba8da65beb5af61dee9718f04623 και ΜΙΑ manual API εκτέλεση ολοκληρώθηκαν.
API run[38907646290](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38907646290) PASS: δύο source owner/public/time verified, official
Shorts tab proof,2 requests/~2 quota units. Linux CI/API job91 tests PASS ανά job·
Windows91 tests/14 isolated checks PASS. OSV audit0 known advisories, με όρια
hash/build-tool/Actions coverage. [Πλήρες report](YOUTUBE_API_CLOUD_VALIDATION.md).

Δεν επαναλαμβάνεις το real API run με την προηγούμενη άδεια. Validation δεν έλαβε
Discord secret και δεν έγραψε production state. MASTER/media OFF, schedule disabled.
Πριν από ΟΠΟΙΟΔΗΠΟΤΕ actual GitHub durable-state write, ακόμη και disposable canary,
Discord integration test ή production activation απαιτείται ξεχωριστή έγκριση.
Shorts/premiere/live-transition και client/media περιορισμοί παραμένουν όπως στο report.

Τα παρακάτω κεφάλαια είναι μελλοντικό runbook· δεν αποτελούν άδεια εκτέλεσης.

## 3. Δημιουργία durable state

Έλεγξε το υπάρχον secret στο Settings → Secrets and variables → Actions. Αν
υπάρχει το DISCORD_WEBHOOK_URL, δεν το αλλάζεις. Δεν ζητείται το URL στη συνομιλία.
Η controlled operations job έχει contents:write μόνο για τη state branch μέσω
Contents API. Έλεγξε αν repository/organization policy ή branch rules το μπλοκάρουν.

Run workflow → operation=initialize, confirmation=INITIALIZE. Αυτό γράφει
notification-state/state.json και δεν στέλνει μήνυμα. Η operation απαιτεί δική σου
εξουσιοδότηση ως εξωτερική GitHub αλλαγή. Αν η branch υπάρχει ήδη, η initialize
αρνείται αντί να σβήσει ιστορικό. Το πρώτο production baseline γίνεται μόνο μετά
από επιτυχή πηγή. Δεν γράφουμε runtime state στο main.

## 4. Ασφαλές baseline και dry run

1. Αφού οι πηγές επαληθευτούν, κάνε εγκεκριμένο config commit master_enabled=true.
2. Run workflow → monitor, live=false. Αποθηκεύει baseline/health/ουρά, χωρίς POST.
3. Run workflow → dryrun. Αποθηκεύει αλλαγές μόνο στη μνήμη και εμφανίζει diagnostics.
4. Επανέλαβε monitor, live=false σε δεύτερο job για να επαληθεύσεις persistence,
   χωρίς να επαναρχικοποιήσεις state. Έλεγξε ότι οι baseline εγγραφές δεν ανακοινώνονται.

Το monitor live=false αλλάζει durable state· το dryrun δεν αλλάζει. Για έλεγχο URL
και media χρησιμοποίησε test/manual live=false. Κενό test URL επιλέγει το
https://www.youtube.com/shorts/DVUoG6SSUUI μόνο για youtube_dayz· άλλος source θα
απορριφθεί αν το owner δεν ταιριάζει.

## 5. Ξεχωριστή έγκριση πραγματικού Discord test

Πριν στείλουμε, εγκρίνεις συγκεκριμένα: μία δοκιμαστική ανακοίνωση youtube_dayz
με το DVUoG6SSUUI και το εγκεκριμένο πρότυπο. Με master/πηγή ON, operation=test,
live=true, confirmation=SEND. Αν είχε ήδη σταλεί/διαγραφεί, χρειάζεται ξεχωριστό
repost=true και REPOST. Δεν υπάρχει master override.

Έλεγξε στο Discord client: ακριβές μήνυμα/emojis/line breaks, username/avatar,
απουσία ανεπιθύμητων mentions, native preview και πιθανό playback. Έλεγξε το
message_id στην durable εγγραφή. Χωρίς αυθεντικό GIF ο έλεγχος είναι κείμενο μόνο.
Όταν δοθούν τα GIF, ενεργοποίησε τη σωστή επισύναψη και κάνε νέο, εγκεκριμένο
media test. Μην χρησιμοποιήσεις την ίδια επιτυχή δοκιμή ως απόδειξη GIF upload.

Για TikTok επέλεξε πραγματικό post του αντίστοιχου source, πρώτα dry run, μετά
έγκριση και πραγματικό test. Έλεγξε preview και ασφαλή fallback original URL.
Κάθε πρόσθετο πραγματικό POST ή edit/delete χρειάζεται την αντίστοιχη ρητή εντολή.

## 6. Production acceptance checklist

- CI + Linux source audit χωρίς μη τεκμηριωμένα failures.
- Durable state survives δύο διαφορετικά jobs και conflict test αποτυγχάνει κλειστά.
- Ίδιο post δεν ξαναστέλνεται χωρίς REPOST, ανεξάρτητες πηγές δεν συγχωνεύονται.
- MASTER OFF και source OFF σταματούν αποστολές· OFF→ON δεν κάνει backlog.
- Real message IDs, κείμενα και προαιρετικά αυθεντικά media επαληθεύονται στον client.
- Queue, retry/429, uncertain και recovery έχουν test evidence και λειτουργικό runbook.
- Γνωστοί περιορισμοί Shorts/premiere/TikTok/previews έχουν κοινοποιηθεί.

## 7. Ενεργοποίηση schedule μόνο μετά από έγκριση

Με επιτυχή ελεγχόμενη δοκιμή και νέα ρητή έγκριση:

1. Μετονόμασε .github/workflows/scheduled.yml.disabled σε scheduled.yml και κάνε push.
2. Settings → Secrets and variables → Actions → Variables: πρόσθεσε
   DVA_PRODUCTION_ENABLED με τιμή true.
3. master_enabled=true και οι επιθυμητές τέσσερις πηγές enabled=true.
4. Παρακολούθησε το πρώτο scheduled run. Στόχος cron 7,37 * * * * UTC, όλο τον χρόνο.
   Στην Ελλάδα αυτό σημαίνει λεπτά :07/:37 κάθε ώρα, ανεξάρτητα από θερινή ώρα.

Οι GitHub εκτελέσεις δεν έχουν SLA ακριβούς χρόνου. Δεν χρησιμοποιούνται keepalive
tricks, paid runners ή artifact storage. Με 60 ημέρες αδράνειας schedule μπορεί να
απενεργοποιηθεί. Διατήρησε ελεγμένη πραγματική δραστηριότητα repository και έλεγχε Actions.

## 8. Αντιμετώπιση rollback

Κλείσε πρώτα DVA_PRODUCTION_ENABLED και master. Περίμενε ενεργά jobs. Κάνε revert
κώδικα/config με νέο commit· κράτησε notification-state. Χρησιμοποίησε το restore
runbook στο OPERATIONS_EL.md, ποτέ initialize πάνω σε state με ιστορικό. Σε
uncertain έλεγξε Discord πριν από οποιαδήποτε επέμβαση. Μην διαγράψεις ιστορικό
ή ανακοινώσεις αυτόματα. Χωρίς γνωστό καλό state μην ανοίξεις αποστολές.
