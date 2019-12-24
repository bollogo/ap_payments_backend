Vue.filter('time_ago', function(val) {
	return dateFns.distanceInWordsToNow(new Date(val));
});

function convertToMoney(value) {
    return value * Math.pow(10, -8);
}

Vue.filter('pretty_money', function(value) {
    return convertToMoney(value).toFixed(2) + ' €';
});
