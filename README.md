# Discord Video Alerts

Αυτόματες ανακοινώσεις για **DayZ / Infinity** και **Milo & Mia** στο ίδιο Discord
κανάλι, με ένα υπάρχον webhook. Python + GitHub Actions, χωρίς να μένει ανοικτό
το Windows PC. Τα μηνύματα και οι ρυθμίσεις αλλάζουν από το GitHub website ή VS Code.

**Τρέχουσα κατάσταση:** τοπική υλοποίηση και mock δοκιμές. Τα τέσσερα προφίλ
ελέγχθηκαν πραγματικά στα Windows. Δεν έχει γίνει deployment, πραγματική αποστολή
Discord ή επαλήθευση Linux runner. **MASTER OFF**, media OFF, schedule ανενεργό.
Το TikTok παραμένει experimental. Δες τον [πλήρη πίνακα](DEVELOPMENT_STATUS.md).

## Τι παρακολουθεί

| Πηγή ρύθμισης | Λογαριασμός |
|---|---|
| youtube_dayz | [DayZMomentsTV](https://www.youtube.com/@DayZMomentsTV) |
| youtube_milo_mia | [milo-and-mia-world](https://www.youtube.com/@milo-and-mia-world) |
| tiktok_dayz | [infinity.projectrp](https://www.tiktok.com/@infinity.projectrp) |
| tiktok_milo_mia | [milo.and.mia.world](https://www.tiktok.com/@milo.and.mia.world) |

Το ίδιο βίντεο σε YouTube και TikTok παράγει ξεχωριστές ανακοινώσεις.
Deduplication: platform + source_id + post_id. Αρχική εκτέλεση και επανενεργοποίηση
δεν στέλνουν ιστορικό περιεχόμενο. Υπάρχει ασφαλής ουρά, όριο ηλικίας 24 ωρών,
καθυστέρηση δημοσίευσης και 10 δευτερόλεπτα μεταξύ πραγματικών μηνυμάτων.

## Πρώτη εγκατάσταση στο GitHub — μετά από έγκριση

1. Έλεγξε το [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) και το
   [πλάνο δοκιμαστικής εγκατάστασης](docs/DEPLOYMENT_EL.md).
2. Εγκρίνεις το push αυτού του συγκεκριμένου τοπικού κώδικα στο υπάρχον repository.
3. Το υπάρχον secret **DISCORD_WEBHOOK_URL** παραμένει στο GitHub. Δεν το
   αντιγράφεις εδώ, στη συνομιλία, σε αρχείο ή σε screenshot.
4. Στο Actions εκτέλεσε **Read-only source compatibility audit** για Linux.
5. Στο **controlled operations** εκτέλεσε initialize με confirmation=INITIALIZE.
   Αυτό δημιουργεί το notification-state branch, χωρίς μήνυμα Discord.
6. Μετά την επαλήθευση πηγών, θέσε master_enabled=true και εκτέλεσε monitor
   με live=false για αποθήκευση του πρώτου ασφαλούς baseline.
7. Για μήνυμα δοκιμής χρειάζεται ξεχωριστή έγκριση. Ξεκίνα με test, live=false.
   Ο πραγματικός έλεγχος χρησιμοποιεί live=true και confirmation=SEND.
8. Ενεργοποίησε το schedule μόνο μετά από επιτυχή έλεγχο και ρητή έγκριση,
   σύμφωνα με τον οδηγό deployment. Στόχος είναι κάθε 30 λεπτά, στα :07 και :37 UTC.

Οι αλλαγές εφαρμόζονται στην επόμενη εκτέλεση. Τοπικές αλλαγές χρειάζονται commit
και push. Μία τεχνική αποτυχία πηγής δεν απενεργοποιεί τις άλλες.

## Καθημερινές αλλαγές

- [config/settings.json](config/settings.json): master/πηγές, usernames, avatars,
  role, media, φίλτρα, delays, retry, logging και health thresholds.
- [config/messages](config/messages): τέσσερα αυθεντικά UTF-8 πρότυπα· κράτησε {VIDEO_URL}.
- [assets](assets): πρόσθεσε τα δικά σου αυθεντικά GIF/εικόνες· δεν έχουν δοθεί ακόμη.
- [Οδηγός λειτουργίας](docs/OPERATIONS_EL.md): πλήρης πίνακας πεδίων, manual/test,
  edit/delete, troubleshooting, restore και rollback.

## Ασφάλεια, κόστος και όρια

Τα @everyone/@here/user mentions απενεργοποιούνται. Προαιρετικό role ping επιτρέπεται
μόνο για το συγκεκριμένο configured ID. Το webhook URL δεν αποθηκεύεται σε state/logs.
Οι αβέβαιες αποστολές κρατούνται ως uncertain και δεν ξαναστέλνονται αυτόματα.
Το state branch και το Git history είναι η durable βάση, όχι cache ή προσωρινό artifact.

Ο στόχος €0/μήνα στηρίζεται σε public repository και δωρεάν standard GitHub runners.
Δεν επιτρέπονται paid APIs/υποδομές. Scheduling delays, μικρό RSS window, TikTok
blocking και αβέβαιη network delivery δεν επιτρέπουν εγγύηση άμεσης ή exactly-once
αποστολής. Τα Shorts-only/premiere φίλτρα και το Discord playback έχουν περιορισμούς.
Δες [έρευνα/συμβατότητα](docs/RESEARCH.md) και [security audit](docs/SECURITY_AUDIT.md).

## Τοπική επαλήθευση για ανάπτυξη

Python 3.12. Χρησιμοποίησε κλειδωμένες δωρεάν dependencies σε τοπικό .venv.
PowerShell, μέσα στο D:\Discord Video Alerts:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.lock
.\.venv\Scripts\python.exe scripts/check_local.py
```

Αυτό δεν στέλνει Discord μηνύματα και δεν γράφει στο GitHub. Για CLI:

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m video_alerts.cli validate
.\.venv\Scripts\python.exe -m video_alerts.cli initialize --confirmation INITIALIZE
.\.venv\Scripts\python.exe -m video_alerts.cli dryrun
```

Η initialize αφορά μόνο τοπικό state όταν λείπει --github. Τοπικά δεν απαιτείται να
αποθηκεύσεις το πραγματικό webhook secret. scripts/setup_dev.py αφορά αλλαγή
dependencies και ανανέωση lock, όχι τη συνήθη αναπαραγωγή δοκιμών.

## Συνέχεια ανάπτυξης

[AGENTS.md](AGENTS.md), [CODEX_CONTEXT.md](CODEX_CONTEXT.md), [HANDOFF.md](HANDOFF.md),
[DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) και [CHANGELOG.md](CHANGELOG.md)
κρατούν απαιτήσεις, αποφάσεις, πραγματικά αποτελέσματα και ακριβή επόμενα βήματα.
Το [MASTER_REQUEST.md](docs/MASTER_REQUEST.md) είναι το αρχικό αίτημα χωρίς αλλαγές.
