# Ελεγχόμενο baseline τεσσάρων πηγών — 2026-10-17

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

Η πραγματική cloud εκτέλεση εκκρεμεί κατά την προετοιμασία αυτού του οδηγού.
Τεχνική σχεδίαση: [PRODUCTION_BASELINE_PLAN.md](PRODUCTION_BASELINE_PLAN.md).
