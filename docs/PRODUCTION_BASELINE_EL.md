# Ελεγχόμενο baseline τεσσάρων πηγών — 2026-10-17

**ΑΠΟΤΥΧΙΑ ΜΕ ΑΣΦΑΛΕΙΑ — Η ΑΔΕΙΑ ΕΞΑΝΤΛΗΘΗΚΕ.** Η μοναδική
[run38984066072](https://github.com/DigitizedInspirations/discord-video-alerts/actions/runs/38984066072)
απέτυχε στο strict public HTML metadata του @infinity.projectrp. Το write step
παραλείφθηκε. Μηδενικές απόπειρες production write και μηδενικά baseline/queued/sent
records. Νέο read-only GitHubStore επαλήθευσε το αρχικό κενό state αμετάβλητο.
ΜΗΝ εκτελέσετε ξανά τη ροή ή source probes και ΜΗΝ επιχειρήσετε επισκευή.

| Πηγή | Πεπερασμένο listing | Metadata | Baselines στην production |
|---|---:|---|---:|
| YouTube DayZ | 6 | Όλα επαληθεύτηκαν μόνο στη μνήμη | 0 |
| YouTube Milo & Mia | 14 | Όλα επαληθεύτηκαν μόνο στη μνήμη | 0 |
| TikTok Infinity | 30 | Αποτυχία· ακριβές πεδίο άγνωστο | 0 |
| TikTok Milo & Mia | 17 | Δεν εκτελέστηκε enrichment | 0 |

156 tests PASS σε Windows/Linux CI/baseline job,14 local simulations PASS. Source
staged audit20 files/0 findings, OSV0 advisories με όρια κάλυψης. YouTube1 API request/
~1 quota unit. MASTER/media/schedule OFF, χωρίς Discord secret/requests ή monitoring.
Επόμενο βήμα μόνο με ΝΕΑ έγκριση για στοχευμένη διάγνωση TikTok και τυχόν fix.
Νέα baseline προσπάθεια απαιτεί νέα ξεχωριστή άδεια μίας εκτέλεσης και νέο preflight.
[Πλήρες τεχνικό αποτέλεσμα και hashes](PRODUCTION_BASELINE_RESULTS.md).

## Ιστορική σχεδίαση — δεν αποτελεί άδεια εκτέλεσης

Εγκρίθηκε ΜΙΑ προσπάθεια μόνο για ιστορικό baseline, με MASTER και πρόγραμμα OFF.
Δεν επιτρέπονται monitoring, Discord, ενεργοποίηση πηγών, backfill, αρχικοποίηση,
restore, επισκευή ή διαγραφή branches. Μην χρησιμοποιήσετε το operate.yml.

Το ειδικό baseline-state.yml ελέγχει το ακριβές αρχικό state, repository/main/SHA,
run και επιβεβαίωση. Μόνο το βήμα metadata λαμβάνει YOUTUBE_API_KEY. Κανένα βήμα
δεν λαμβάνει Discord secret. Τα βήματα state λαμβάνουν μόνο GitHub token.

Οι τέσσερις πηγές είναι youtube_dayz, youtube_milo_mia, tiktok_dayz και
tiktok_milo_mia. Όλα τα videos του πεπερασμένου παραθύρου κάθε πηγής απαιτούν
επαληθευμένα URL, κάτοχο, δημόσια πρόσβαση και χρόνο δημοσίευσης. Τα παράθυρα ΔΕΝ
αποτελούν πλήρες ιστορικό λογαριασμού. Άγνωστα Shorts/premiere δεν επινοούνται.

Μόνο αν περάσουν και οι τέσσερις πηγές επιτρέπεται ΕΝΑ optimistic-SHA update του
state.json στο υπάρχον notification-state. Αποθηκεύονται μόνο baseline records,
με μηδενικά attempts και χωρίς message IDs/queues/sends. Οι πηγές παραμένουν
ανενεργές και απαιτούν νέο ασφαλές resume baseline σε μελλοντική ενεργοποίηση.
Διατηρούνται το αρχικό instance ID και η ημερομηνία δημιουργίας. Νέο read-only
GitHubStore επαληθεύει το αποτέλεσμα ανεξάρτητα.

Σε αποτυχία έστω μίας πηγής δεν γίνεται production write. Σε αποτυχία ή αβέβαιη
απάντηση ΔΕΝ επαναλαμβάνεται run ή write· απαιτείται νέα έγκριση μετά από έλεγχο.
Η άδεια εξαντλείται και σε αποτυχημένη προσπάθεια. Το TikTok παραμένει πειραματικό.
Το Smart Monitoring Schedule παραμένει μελλοντικό τελικό στάδιο, χωρίς υλοποίηση.

Η πραγματική cloud εκτέλεση απέτυχε όπως καταγράφεται παραπάνω. Καμία επανάληψη.
Τεχνική σχεδίαση: [PRODUCTION_BASELINE_PLAN.md](PRODUCTION_BASELINE_PLAN.md).
