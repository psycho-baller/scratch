import open from 'open';

const baseObsidianUri = 'obsidian://actions-uri';
const baseDailyNoteUri = `${baseObsidianUri}/daily-note`;
const baseWeeklyNoteUri = `${baseObsidianUri}/weekly-note`;
const uris = {
  dailyNote: {
    open: `${baseDailyNoteUri}/open-current`,
    prepend: `${baseDailyNoteUri}/prepend?create-if-not-found=true&ensure-newline=true&content=`,
    append: `${baseDailyNoteUri}/append?create-if-not-found=true&ensure-newline=true&content=`,
  },
  weeklyNote: {
    open: `${baseWeeklyNoteUri}/open-current`,
    get: `${baseWeeklyNoteUri}/get-current`,
    prepend: `${baseWeeklyNoteUri}/prepend?create-if-not-found=true&ensure-newline=true&content=`,
    append: `${baseWeeklyNoteUri}/append?create-if-not-found=true&ensure-newline=true&content=`,
  },
};

function addVaultToUri(uri) {
  const vault = "Obsidian"
  if (uri.includes('?')) {
    return uri + `&vault=${vault}`;
  }
  return uri + `?vault=${vault}`;
}

function openDailyNote() {
  const uri = addVaultToUri(uris.dailyNote.open);
  const uriWithVault = uri;
  const url = encodeURI(uriWithVault);
  console.log(`Opening ${url}`);
  open(url);
}

function prependToDailyNote(note) {
  const uriWithVault = addVaultToUri(uris.dailyNote.prepend + note)

  const url = encodeURI(uriWithVault + '&below-headline="#### Reflection"')
  console.log(`Opening ${url}`);
  open(url);
}

function appendToDailyNote(note) {
  const uriWithVault = addVaultToUri(uris.dailyNote.append + note)

  const url = encodeURI(uriWithVault) + '&below-headline=#### Reflection'
  console.log(`Opening ${url}`);
  open(url);
}

async function getWeeklyNote() {
  const uri = uris.weeklyNote.get + `?x-success=http://localhost:3000
  &x-error=http://localhost:3000`
  const uriWithVault = addVaultToUri(uri)
  const url = encodeURI(uriWithVault)
  console.log(`Opening ${url}`);
  return await open(url);
}


// openDailyNote();
// appendToDailyNote('Hey mom!');
console.log(getWeeklyNote());
