# Ελεγχόμενη εγκατάσταση — canary αποτέλεσμα 2026-10-16

> ΝΕΑ έγκριση: διορθωμένο dict guard και ΜΙΑ νέα ελεγχόμενη initialization.
>138 tests/14 simulations PASS, ακόμη χωρίς dispatch/write. MASTER/schedule OFF.
> [Τρέχον scope και όρια](PRODUCTION_INITIALIZATION_RETRY_EL.md). Όχι baseline/Discord/monitoring/activation.


Ο isolated GitHub canary πέρασε14 cloud checks σε δύο fresh runners μόνο στο
`dva-canary-20261016-0f9d3a7c`. [Report](DURABLE_CANARY_RESULTS.md). Windows104
tests/14 filesystem checks και Linux104 tests ανά job PASS. Branch διατηρείται·
δύο runs εξαντλήθηκαν. Όχι νέα runs/writes/cleanup χωρίς έγκριση. Το προηγούμενο
μοναδικό API run38907646290 PASS με2 requests/~2 units και για τις δύο πηγές.
[API report](YOUTUBE_API_CLOUD_VALIDATION.md). Δεν επαναλαμβάνεται.

Production notification-state ανέγγιχτο·0 production/Discord/YouTube requests στον
canary, κανένα service secret. MASTER/media OFF, schedule disabled. Production
initialize/baseline/restore, Discord και activation απαιτούν νέα έγκριση. Παραμένουν
όρια premiere/live transitions, TikTok και client/media. Τα παρακάτω είναι μελλοντικό
runbook, όχι εξουσιοδότηση εκτέλεσης.

## 3. Δημιουργία durable state

Προετοίμασε/έλεγξε ξεχωριστό state-only workflow χωρίς Discord/YouTube secrets.
Μην χρησιμοποιήσεις το γενικό operations job για αυτόν τον περιορισμένο έλεγχο.
Μετά από νέα ρητή έγκριση, έλεγξε αν υπάρχει notification-state και αρνήσου overwrite.
Αρχικοποίησε μόνο κενό checksum state και επαλήθευσε ανεξάρτητα την ανάκτησή του.
Μην γράφεις runtime state στο main. MASTER/schedule OFF. Έλεγξε repository/
organization policies και branch rules χωρίς χαλάρωση. Baseline και Discord
απαιτούν ξεχωριστό scope. Το υπάρχον webhook secret δεν αλλάζει ούτε εμφανίζεται.

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
