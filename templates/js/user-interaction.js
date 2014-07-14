console.log('Hello from the ui script');

$.getScript('http://cdnjs.cloudflare.com/ajax/libs/typeahead.js/0.10.4/typeahead.bundle.min.js');

var feelings = [
	{name: 'hate', category: 'negative'},
	{name: 'disappointing', category: 'negative'},
	{name: 'lacking', category: 'negative'},
	{name: 'meh', category: 'indifferent'},
	{name: 'whatever', category: 'indifferent'},
	{name: 'love', category: 'positive'}
];

var substringMatcher = function(strs) {
  return function findMatches(q, cb) {
    var matches, substrRegex;
    console.log(q);

    // an array that will be populated with substring matches
    matches = [];

    // regex used to determine if a string contains the substring `q`
    substrRegex = new RegExp(q, 'i');

    // iterate through the pool of strings and for any string that
    // contains the substring `q`, add it to the `matches` array
    $.each(strs, function(i, str) {
      console.log(str);
      if (substrRegex.test(str.name)) {
        // the typeahead jQuery plugin expects suggestions to a
        // JavaScript object, refer to typeahead docs for more info
        matches.push(str);
      }
    });

    cb(matches);
  };
};

$('#feeling').typeahead(
	{
		minLength: 1
	},
	{
		name: 'feelings',
		displayKey: 'name',
		source: substringMatcher(feelings)
	});