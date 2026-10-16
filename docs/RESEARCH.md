# Έρευνα και συμβατότητα — 11 Οκτωβρίου 2026

Οι μετρήσεις είναι τοπικές στα Windows. Δεν έχει γίνει ακόμη push, εκτέλεση σε
GitHub-hosted Linux runner ή πραγματική κλήση στο Discord.

## YouTube

| Πηγή | Επαληθευμένο Channel ID | RSS |
|---|---|---|
| @DayZMomentsTV | UCz5ka9rKYsdaeaxmN_7nHbg | DayZ Moments, 1 εγγραφή |
| @milo-and-mia-world | UCg1uoL9TtAaxvyn6dbQ08fA | Milo & Mia World, 14 εγγραφές |

Η αντιστοίχιση προφίλ→ID και τα επίσημα Atom feeds διαβάστηκαν πραγματικά.
Τα metadata της νεότερης εγγραφής ανά κανάλι ελέγχθηκαν μέσω yt-dlp, με
επαλήθευση channel_id, public availability και timestamp. Το εγκεκριμένο Short
DVUoG6SSUUI ανήκει πράγματι στο DayZ Moments. Δεν είναι νέο test discovery.
Το feed χρησιμοποιεί top-level channel ID χωρίς UC· ο adapter το κανονικοποιεί.

Το RSS δεν ταξινομεί Shorts, κανονικά βίντεο, livestreams ή premieres. Το yt-dlp
παρέχει live_status/was_live και ο adapter αποκλείει live/αρχειοθετημένα live όταν
το φίλτρο είναι ON. Δεν χρησιμοποιείται διάρκεια ή μορφή URL ως απόδειξη Shorts.
Shorts/regular ταξινομούνται με θετική συμμετοχή στις επίσημες source tabs, με
root Channel ID verification. Και τα δύο νεότερα βίντεο επαληθεύτηκαν ως Shorts.
Οι καρτέλες περιορίζονται σε 30 εγγραφές: απουσία δεν αποδεικνύει κατηγορία.
Εκτός αυτού του window το φίλτρο παραμένει PARTIAL και unknown→waiting_metadata.
Η αναγνώριση premiere παραμένει PARTIAL. Το προεπιλεγμένο both επιτρέπει
δημόσια μη-live βίντεο με άγνωστη κατηγορία. Ορισμένα premieres μπορεί να εκτεθούν
ως live από τον πάροχο· χρειάζεται πραγματικό fixture πριν θεωρηθεί πλήρης υποστήριξη.
Scheduled/unavailable εγγραφές επανελέγχονται μέχρι να επιβεβαιωθούν δημόσιες, με
τον πραγματικό release timestamp όταν διατίθεται. Η μετάβαση scheduled→public
δεν έχει δοκιμαστεί σε πραγματικό νέο upload.

Τα feeds είναι πεπερασμένα. Δεν εγγυώνται ανάκτηση όλων των βίντεο μετά από
μεγάλη διακοπή ή μεγάλη συχνότητα δημοσιεύσεων. Άγνωστος χρόνος δημοσίευσης
δεν μετατρέπεται σε «τώρα». Δεν υπάρχει πληρωμένο YouTube API.

Μεταγενέστερο πραγματικό audit έδωσε RSS404 και για τα δύο feeds, ενώ το επόμενο
επανήλθε. Δεν αντιμετωπίστηκε ως άδειο feed. Προστέθηκε public channel listing
fallback με strict root/entry ID, χωρίς login/cookies. Ο fallback είναι mock-tested,
αλλά δεν χρειάστηκε στην τελευταία πραγματική εκτέλεση (official_rss). Τα νέα
adapter audits αρχειοθετούνται στο docs/probes ώστε να διατηρούνται checkpoints.

## TikTok

Τα δύο δημόσια προφίλ έδωσαν HTTP 200. Αυτό από μόνο του δεν αρκεί για monitoring.
Ο πραγματικός yt-dlp profile adapter απαρίθμησε 30 πρόσφατες εγγραφές DayZ και
11 Milo & Mia. Η per-video εξαγωγή του yt-dlp απέτυχε ακόμη και με
ignore_no_formats_error, επομένως δεν χρησιμοποιείται για per-video metadata.

Ελέγχθηκε το δημόσιο HTML των συγκεκριμένων post URLs. Περιέχει
__UNIVERSAL_DATA_FOR_REHYDRATION__ → webapp.video-detail με statusCode=0,
σωστό id, author.uniqueId, createTime και privacy flags. Ο adapter διαβάζει μόνο
αυτά τα δημόσια στοιχεία, ελέγχει λογαριασμό/ID/ιδιωτικότητα και δεν κατεβάζει media.
Άγνωστα/ελλιπή πεδία ή CAPTCHA σελίδα αποτυγχάνουν κλειστά. Δεν χρησιμοποιούνται
cookies, credentials, CAPTCHA bypass ή υπογεγραμμένα ιδιωτικά APIs.

Η συγκεκριμένη διαδρομή είναι experimental: το δημόσιο HTML και η πρόσβαση από
datacenter IPs μπορεί να αλλάξουν. Το docs/adapter_probe.json είναι η τελική
πραγματική τοπική μέτρηση. Linux συμβατότητα: NOT TESTED μέχρι source-audit.yml.
Το profile listing περιορίζεται στις πρώτες 30 εγγραφές. Οι πηγές είναι ανεξάρτητες.

## Discord previews και media

Τα αρχικά URLs παραμένουν στο κανονικό message content για native previews.
Το disabled χρησιμοποιεί <URL> και SUPPRESS_EMBEDS. Ένα προσαρμοσμένο embed
δεν δημιουργεί αυθαίρετο video player. Η δυνατότητα playback εξαρτάται από
Discord client, πλατφόρμα και ρυθμίσεις του server και δεν έχει επαληθευτεί.
GIF/image attachment και native video preview μπορεί να συνυπάρξουν διαφορετικά
ανά client· απαιτείται ο εγκεκριμένος πραγματικός έλεγχος.

Εξετάστηκε το [vxtiktok](https://github.com/dylanpdx/vxtiktok), το οποίο εμφανίζεται
ως archived project. Δεν επελέγη: τρίτος πάροχος βλέπει τα links και τα client
requests, η διαθεσιμότητα/κόστος/ιδιωτικότητα δεν έχουν επιβεβαιωθεί. External
embed services παραμένουν NOT TESTED και δεν ενεργοποιούνται σιωπηρά.
Επιλογή τέτοιας υπηρεσίας χρειάζεται ξεχωριστή αξιολόγηση και έγκριση αλλαγής ρύθμισης.

Δεν δόθηκαν αυθεντικά GIF/avatars. Η επαλήθευση media έγινε με συνθετικά αρχεία
μόνο στις δοκιμές, όχι ως branding. Discord uploads δεν έχουν δοκιμαστεί πραγματικά.

## Persistence, κόστος και GitHub

Επιλέχθηκε ξεχωριστό notification-state branch, checksum envelope, optimistic
SHA writes μέσω Contents API και κοινό workflow concurrency group. Το commit
history είναι durable backup· δεν στηριζόμαστε σε caches/artifacts. Πριν από κάθε
POST αποθηκεύεται sending. Μη επιβεβαιωμένη αποστολή γίνεται uncertain και δεν
ξαναστέλνεται αυτόματα. Exactly-once δεν είναι εφικτό μετά από αμφίσημη δικτυακή
αποτυχία. Νεότερα delivery tombstones διατηρούνται κατά restore.

Τοπικά χρησιμοποιούνται atomic replace, fsync, checksum, backup και CLI lock.
Cloud πραγματικές εγγραφές/ανάκτηση: NOT TESTED. Για corrupt/missing state file
σε υπάρχουσα branch, explicit restore από εγκεκριμένο SHA επικυρώνει backup,
κάνει τις παλιές εκκρεμείς αποστολές uncertain και απαιτεί νέο safe baseline.
Valid current state διατηρεί νεότερες deliveries· διαφορετικό instance απορρίπτεται.
Missing branch χρειάζεται reviewed Git repair. Η βάση και το ιστορικό μεγαλώνουν·
παρακολούθησε μέγεθος state.json και όρια repository/Contents API πριν από χρόνια
λειτουργίας. Δεν υπάρχει αυτόματη διαγραφή ιστορικού ή rewrite της state branch.

Τα standard GitHub-hosted runners σε public repositories παρέχονται δωρεάν.
Δεν απαιτείται το Windows PC online. Η βάση είναι public και περιέχει δημόσια post
metadata/message IDs/health μόνο, όχι secrets. Αλλαγή σε private repository ή paid
runner χρειάζεται νέα αξιολόγηση κόστους. Δεν χρησιμοποιούνται hosted artifacts.
Τα schedules μπορεί να καθυστερήσουν ή να παραλειφθούν· minute-zero αποφεύγεται.
Σε public repositories scheduled workflows απενεργοποιούνται μετά από 60 ημέρες
αδράνειας repository. Μην θεωρήσεις τα state commits εγγυημένο keepalive.

## Πρωτογενείς πηγές

- [GitHub scheduling και inactivity](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Repository Contents API](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents)
- [GitHub concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [Discord webhook API](https://docs.discord.com/developers/resources/webhook#execute-webhook)
- [Discord rate limits](https://docs.discord.com/developers/topics/rate-limits)
- [yt-dlp source](https://github.com/yt-dlp/yt-dlp)
- [TikTok extractor source](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/tiktok.py)
