const get_api_endpoint = (collection_name) =>
	`/api/fetch_data/?collection_name=${
		encodeURIComponent(collection_name)
	}`;

const fetch_collection_data = (collection_name, container) =>
	fetch(get_api_endpoint(collection_name)).then(result =>
		result.text().then(content => (
				container.innerHTML = content
			),
		)).catch(error => {
		alert('Unexpected error occurred while fetching data');
		throw new Error(error);
	});

(
	() => {

		const search_box = document.getElementsByClassName(
			'search_box',
		)[0];

		const collections = Object.values(
			document.getElementsByClassName(
				'collection',
			),
		).map(collection => [
			collection, collection.getAttribute('data--name'),
		]);

		document.getElementsByClassName(
			'list_of_collections',
		)[0].addEventListener('click', (event) => {

			const collection = event.target.closest('.collection');

			if (collection === null)
				return true;

			event.preventDefault();

			const collection_name = event.target.closest(
				'.collection_name',
			);

			if (collection_name !== null)
				collection.classList.toggle('closed');

			const collection_content = collection.getElementsByClassName(
				'collection_content',
			)[0];

			if (collection_content.innerHTML === '')
				void fetch_collection_data(
					collection.getAttribute('data--name'),
					collection_content,
				);

		});

		document.body.addEventListener(
			'keyup',
			(event) => {

				if (!event.target.contains(search_box))
					return;

				const filter_value = search_box.value;

				collections.map(([
						collection,
						collection_name,
					]) =>
						collection_name.substr(
							0,
							filter_value.length,
						) === filter_value ?
							collection.classList.remove('hidden') :
							collection.classList.add('hidden'),
				);


			},
		);

	}
)();