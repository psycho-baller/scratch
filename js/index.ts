const getKey = (r: number, c: number) => {
	// make it unique for each soduku cell
	const cellKeyRow = Math.floor(r / 3);
	const cellKeyCol = Math.floor(c / 3);
	return `${cellKeyRow}-${cellKeyCol}`;
};

const main = () => {
	const input = [
		["8", "3", ".", ".", "7", ".", ".", ".", "."],
		["6", ".", ".", "1", "9", "5", ".", ".", "."],
		[".", "9", "8", ".", ".", ".", ".", "6", "."],
		["8", ".", ".", ".", "6", ".", ".", ".", "3"],
		["4", ".", ".", "8", ".", "3", ".", ".", "1"],
		["7", ".", ".", ".", "2", ".", ".", ".", "6"],
		[".", "6", ".", ".", ".", ".", "2", "8", "."],
		[".", ".", ".", "4", "1", "9", ".", ".", "5"],
		[".", ".", ".", ".", "8", ".", ".", "7", "9"],
	];

	const hMap = new Map();
	for (let r = 0; r < 9; r++) {
		for (let c = 0; c < 9; c++) {
			const key = getKey(r, c);
			const val = input[r][c];
			if (val === ".") {
				continue;
			}
			if (!hMap.has(key)) {
				hMap.set(key, new Set());
			}
			const set = hMap.get(key);
			if (set.has(val)) {
				return false;
			}
			set.add(val);
		}
	}
	return true;
};

console.log(main());
