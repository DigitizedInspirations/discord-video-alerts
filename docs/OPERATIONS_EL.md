# Οδηγός λειτουργίας και αντιμετώπισης προβλημάτων

## Ρυθμίσεις από το GitHub

1. Άνοιξε το repository και το config/settings.json.
2. Πάτησε το μολύβι για επεξεργασία.
3. Άλλαξε μόνο τις επιθυμητές τιμές, κράτησε εισαγωγικά και κόμματα, κάνε commit.
4. Εκτέλεσε Actions → controlled operations → validate.
5. Οι νέες ρυθμίσεις εφαρμόζονται στην επόμενη εκτέλεση. Δεν αλλάζουν ήδη τρέχον job.

| Ρύθμιση | Τι κάνει |
|---|---|
| master_enabled | true: επιτρέπει αυτόματες αποστολές· false: καθολικό OFF |
| channels.<πηγή>.enabled | ανεξάρτητο ON/OFF για μία από τις τέσσερις πηγές |
| queue_delay_seconds | απόσταση μεταξύ πραγματικών ανακοινώσεων, default 10 |
| max_messages_per_run | όριο αποστολών ανά job, default 5 |
| max_video_age_hours | μέγιστη ηλικία αυτόματου βίντεο, default 24 |
| publication_delay_minutes | αναμονή από τη δημοσίευση, ανεξάρτητη ανά πηγή |
| template | διαδρομή του επεξεργάσιμου UTF-8 μηνύματος |
| username / avatar_url | ταυτότητα webhook ανά μήνυμα, χωρίς νέο webhook |
| avatar_fallback | omit: βασικό avatar webhook· skip: δεν στέλνει αν avatar μη έγκυρο |
| media.enabled / path | επισύναψη πραγματικού τοπικού GIF/PNG/JPEG/WEBP |
| media.require_animation | true απαιτεί έγκυρο πολυκαρέ GIF· false επιτρέπει στατική εικόνα |
| media.max_bytes | upload ceiling έως 10 MB, όχι εγγύηση ορίου κάθε server |
| media.fallback | omit: μόνο κείμενο· skip: διατήρηση ουράς και αναφορά προβλήματος |
| role.enabled / id | προαιρετικό role ping, OFF αρχικά, ID ως string |
| preview | native ή disabled· playback χρειάζεται πραγματική δοκιμή |
| embed.enabled / color | προαιρετικό embed με χρώμα σε δεκαδικό RGB integer |
| filters.enabled | ενεργοποίηση των φίλτρων της πηγής |
| filters.include_keywords | απαιτεί τουλάχιστον μία λέξη στον τίτλο, χωρίς διάκριση πεζών |
| filters.exclude_keywords | αποκλείει τίτλο που περιέχει οποιαδήποτε λέξη |
| filters.video_types | both, shorts ή regular· positive official-tab proof, unknown εκτός finite window αναβάλλεται |
| filters.exclude_livestreams | default true· αποκλείει live και archived live |
| filters.exclude_premieres | default false· άγνωστη ταξινόμηση αναβάλλεται αν ζητηθεί true |
| retry | περιορισμένες προσπάθειες, backoff/jitter και ανώτατη αναμονή |
| health.failure_threshold | αποτυχίες πριν FAILED και μοναδική προειδοποίηση summary |
| logging.level | INFO για αναλυτικά events, WARNING για προβλήματα |

Το master δεν αλλάζει τα επιμέρους enabled. OFF ακυρώνει υπάρχουσες εκκρεμείς
ανακοινώσεις της αντίστοιχης πηγής. OFF→ON δημιουργεί ασφαλές baseline και δεν
ανακοινώνει περιεχόμενο της περιόδου OFF. Τεχνική αποτυχία αφήνει την πηγή ON και
επιτρέπει ανάκτηση πρόσφατων δημοσιεύσεων έως το age limit. Το OFF εφαρμόζεται
όταν μια εκτέλεση διαβάσει τη ρύθμιση· δεν ανιχνεύεται ενδιάμεσο toggle που άλλαξε
ξανά πριν οποιαδήποτε εκτέλεση. Με resume outage πριν ολοκληρωθεί το baseline,
η πρώτη επιτυχής λίστα θεωρείται baseline για ασφάλεια, επομένως μπορεί να χαθούν
ανακοινώσεις εκείνου του αρχικού διαστήματος.

Οι καθυστερήσεις δημοσίευσης αποθηκεύονται στην ουρά, χωρίς πολύωρα sleeps.
Η αναμενόμενη ανακοίνωση είναι στο επόμενο πραγματικό poll αφού γίνει eligible,
όχι εγγυημένα ακριβώς στο 30λεπτο ή στο λεπτό της configured delay.

## Επεξεργασία μηνυμάτων

Άνοιξε config/messages/<πηγή>.txt. Διατήρησε {VIDEO_URL}. Μπορείς να προσθέσεις
{VIDEO_TITLE}, {CHANNEL_NAME}, {PLATFORM}, {PUBLISHED_AT}. Δεν επιτρέπονται άλλα
placeholders, format specs ή εκτέλεση κώδικα. Τα εξωτερικά metadata καθαρίζονται
και δεν επιτρέπουν @everyone/@here/user pings. Role ping επιτρέπεται μόνο για
το συγκεκριμένο ID στη ρύθμιση. Το role πρέπει να είναι mentionable ή να υπάρχουν
τα αντίστοιχα Discord δικαιώματα· ο πραγματικός client έλεγχος εκκρεμεί.

## Χειροκίνητη ανακοίνωση και test

Actions → controlled operations → Run workflow:

1. Διάλεξε manual ή test και τη σωστή πηγή.
2. Βάλε το URL. Για test με κενό URL χρησιμοποιείται το εγκεκριμένο DayZ Short.
3. Κράτησε live=false για προεπισκόπηση. Δεν γίνεται αποστολή ή durable state write.
4. Έλεγξε payload, ταυτότητα, media και duplicate ένδειξη στο log.
5. Μόνο αφού εγκριθεί: live=true και confirmation=SEND.
6. Για ήδη ανακοινωμένο/διαγραμμένο post απαιτούνται repost=true και REPOST.

MASTER και η πηγή πρέπει να είναι ON για πραγματική χειροκίνητη αποστολή.
Το manual/test επαληθεύει πηγή και public status, αλλά σκόπιμα παρακάμπτει
age/filter/publication-delay περιορισμούς: επιλέγεις συγκεκριμένο βίντεο.
Baseline/filtered εγγραφή χωρίς προηγούμενη delivery μπορεί να σταλεί με SEND.
Uncertain δεν παρακάμπτεται ούτε με REPOST. Test δεν αναγνωρίζεται ως νέα δημοσίευση.
Το use_template=false στέλνει μόνο το canonical URL με τις ίδιες ασφαλείς mention/media
ρυθμίσεις. Τα URLs YouTube επαληθεύονται μέσω Channel ID, τα TikTok μέσω username/ID.

## Εύρεση, edit και delete

Με show βάλε source και post_id. Η εγγραφή εμφανίζει status, timestamp, attempts
και message_id. Με edit χρειάζεται confirmation=EDIT. Με delete χρειάζεται DELETE.
Δεν χρειάζεται live=true για edit/delete· το όνομα της λειτουργίας και η confirmation
αποτελούν την ρητή εξουσιοδότηση. Ισχύουν μόνο για μηνύματα του συγκεκριμένου webhook.
Το edit ξαναχρησιμοποιεί το τρέχον πρότυπο και αντικαθιστά τα attachments. Το delete
κρατά tombstone, ώστε το βίντεο να μην ανακοινωθεί ξανά. Δεν διαγράφεται ανακοίνωση
αυτόματα όταν αποσυρθεί το βίντεο. Edit/delete από άλλους στο Discord δεν ενημερώνουν
αυτόματα τη βάση. Σε αβέβαιη απάντηση επανάλαβε μόνο μετά από έλεγχο client:
delete είναι idempotent (404 αντιμετωπίζεται ως ήδη διαγραμμένο), edit αντικαθιστά το ίδιο ID.

## Health, λάθη και ανάκτηση

Στο Actions Summary βλέπεις κάθε πηγή χωριστά: HEALTHY, DEGRADED, FAILED,
DISABLED ή NOT VERIFIED, επιτυχείς ελέγχους και συνεχόμενες αποτυχίες. Τα πλήρη
last_attempt/last_detected/last_announcement είναι στη state branch. Τα alerts
παραμένουν στα logs/summary, επειδή δεν έχει δοθεί ξεχωριστός διαχειριστικός
προορισμός· δεν γεμίζουν το δημόσιο Discord με system errors.

| Πρόβλημα | Ενέργεια |
|---|---|
| configuration validation | διόρθωσε μόνο το επισημασμένο πεδίο· δεν υπάρχει silent default |
| TikTok CAPTCHA/blocked/HTML changed | άφησε τα YouTube ενεργά, εκτέλεσε source audit, μη δώσεις cookies |
| unknown Shorts/premiere | κράτησε both ή περίμενε επαληθευμένη ταξινόμηση· καμία εικασία |
| media missing/invalid | πρόσθεσε αυθεντικό σωστό αρχείο ή βάλε enabled=false |
| HTTP 401/403 Discord | έλεγξε το υπάρχον secret μέσα στο GitHub, όχι στη συνομιλία |
| HTTP 429 | η ουρά σέβεται Retry-After και μεταθέτει υπερβολική αναμονή στο επόμενο job |
| uncertain/sending μετά από crash | έλεγξε Discord· δεν υπάρχει αυτόματο resend |
| GitHub 409 state write | σταμάτησε αποστολές, περίμενε άλλο job και έλεγξε το concurrency |
| missing/corrupt state | μη χρησιμοποιήσεις initialize πάνω σε ιστορικό· κάνε recovery |
| source FAILED | δες σφάλμα συγκεκριμένης πηγής· η ολοκλήρωση του job δεν σημαίνει επιτυχία της |

Αν uncertain μήνυμα υπάρχει στο Discord, ενεργοποίησε Developer Mode στις
Discord ρυθμίσεις και αντέγραψε το Message ID του συγκεκριμένου μηνύματος.
Run workflow → resolve, source/post_id, message_id, confirmation=RESOLVE.
Γίνεται GET μέσω του ίδιου webhook και απαιτείται το σωστό URL στο content.
Τότε καταγράφεται sent χωρίς νέο POST. Δεν απαιτεί live=true. Λανθασμένο ID/URL
δεν αλλάζει state. Αν δεν βρίσκεις μήνυμα, κράτησε uncertain για reviewed recovery·
η απουσία δεν θεωρείται απόδειξη ότι δεν παραδόθηκε.

Για ασφαλές cloud restore: MASTER OFF, όλοι οι runners σταματημένοι, άνοιξε
notification-state → History, διάλεξε πλήρες commit SHA. Run workflow → restore,
restore_ref=<SHA>, confirmation=RESTORE. Η λειτουργία επικυρώνει checksum και
instance ID και διατηρεί νεότερες delivery/tombstone εγγραφές. Δεν κάνει POST.
Αυτό προστατεύει από rollback που θα διπλοέστελνε ήδη ανακοινωμένα βίντεο.
Για corrupt/missing state file σε υπάρχουσα branch, explicit restore από valid
checkpoint κρατά παλιές εκκρεμείς εγγραφές uncertain και απαιτεί νέο baseline.
Μπορεί να χαθούν ανακοινώσεις μετά το backup: αποφεύγονται αυτόματες διπλοαποστολές.
Missing branch ή HTTP403/409 σταματά την ανάκτηση, χωρίς αυτόματη initialize.

Τοπικά: backup βρίσκεται στο state/state.backup.json. CLI restore με filename
και RESTORE διατηρεί αντίγραφο pre-restore. Αν το current state λείπει/είναι corrupt,
οι εκκρεμείς αποστολές του backup γίνονται uncertain και απαιτείται νέο safe baseline.
Πριν αφαιρέσεις stale state/operator.lock, βεβαιώσου ότι δεν τρέχει Python job.

## Rollback και ενημερώσεις

Για διακοπή παραγωγής βάλε DVA_PRODUCTION_ENABLED=false στο repository variable
και master_enabled=false σε νέο commit. Περίμενε τυχόν ενεργό job: οι αλλαγές
δεν εφαρμόζονται στη μέση ήδη τρέχουσας εκτέλεσης. Μην διαγράψεις state branch.
Επαναφορά κώδικα γίνεται με νέο revert commit, όχι reset του delivery history.
Dependencies ενημερώνονται μόνο με νέες δοκιμές/adapters audit και ανανέωση lock.
Αν το schedule απενεργοποιηθεί λόγω 60 ημερών αδράνειας, άνοιξε Actions και
ενεργοποίησέ το ξανά αφού ελέγξεις state και max age. Παρακολούθησε το Actions
tab περιοδικά· δεν έχει εξουσιοδοτηθεί paid uptime service.
