# Ελεγχόμενη εγκατάσταση — δεν έχει ακόμη πραγματοποιηθεί

## 1. Συγκεκριμένη έγκριση push

Το τοπικό πακέτο περιλαμβάνει κώδικα, config, εγκεκριμένα πρότυπα, tests, guides,
χειροκίνητα workflows και ανενεργό scheduled.yml.disabled. Μόνο μετά από έγκριση:
commit και push στο υπάρχον DigitizedInspirations/discord-video-alerts. Το master
παραμένει false, οι επισυνάψεις false και δεν ενεργοποιείται schedule.
Το CI θα εκτελέσει mock tests χωρίς πρόσβαση στο Discord secret. Έλεγξε ότι το
repository παραμένει public και χρησιμοποιούνται μόνο ubuntu-latest standard runners.

## 2. Επαλήθευση Linux χωρίς Discord

1. Άνοιξε Actions → Read-only source compatibility audit → Run workflow.
2. Έλεγξε discovery/metadata/public/owner/timestamp και των τεσσάρων πηγών.
3. Αν το TikTok αποτυγχάνει σε runner, κατέγραψε το ως BLOCKED Linux. Δεν
   παρακάμπτεις CAPTCHA/credentials. Άφησε τα YouTube ανεξάρτητα και λειτουργικά.
4. Οι ισχύουσες απαιτήσεις των τεσσάρων πηγών διατηρούνται· δεν θεωρείται έγκριση
   αφαίρεσης του TikTok. Απόφαση μερικής παραγωγής απαιτεί ρητή έγκριση.

Το audit δεν παίρνει webhook secret ούτε contents:write. Προσωρινά αρχεία report
φαίνονται στα logs του job και δεν χρησιμοποιούνται ως durable notification state.

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
