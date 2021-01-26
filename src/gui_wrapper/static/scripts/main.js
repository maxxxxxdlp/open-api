const get_parameter_value = (parameter_element, parameter_type) =>
	parameter_type === 'string' ?
		parameter_element.getElementsByTagName('input')[0].value :
		(
			parameter_element.getElementsByTagName('input')[0].checked
		).toString();

const fetch_parameters_data = (parameters) =>
	path_detailed_info[4].forEach((parameter, index) => (
		path_detailed_info[4][index][7] = get_parameter_value(parameters[index], parameter[5])
	));

const create_request_url = () =>
	path_detailed_info[4].reduce((request_url, parameter_data) =>
			parameter_data[6] === 'path' ?
				request_url.replace(`{${parameter_data[0]}}`, encodeURIComponent(parameter_data[7])) :
				`${request_url}${parameter_data[0]}=${parameter_data[7]}&`,
		`${path_detailed_info[1]}${path_detailed_info[0]}?`);

const expose_request_url = (request_url_element, request_url) =>
	request_url_element.classList.remove('hidden') ||
	(
		request_url_element.getElementsByTagName('input')[0].value = request_url
	);

const show_loading_animation = (response_container) =>
	response_container.classList.remove('hidden') ||
	response_container.classList.add('loading');

const show_response = (response_container, response)=>
	response_container.classList.remove('loading') ||
	response.text().then(response_html=>(
		response_container.getElementsByClassName('response_content')[0].innerHTML=response_html
	));

(
	() => {

		const parameters = Object.values(document.getElementsByClassName('parameter'));
		const request_url_element = document.getElementsByClassName('request_url')[0];
		const response_container = document.getElementById('response');

		document.body.addEventListener('change', (event) => {

			const parameter_examples = event.target.closest('.parameter_examples');
			if (parameter_examples !== null && parameter_examples.value !== '0')
				parameter_examples.parentElement.nextElementSibling.getElementsByTagName('input')[0].value =
					parameter_examples.value;

		});

		document.body.getElementsByClassName('execute_button')[0].addEventListener('click', () => {

			fetch_parameters_data(parameters);
			const request_url = create_request_url();
			expose_request_url(request_url_element, request_url);
			show_loading_animation(response_container);
			fetch(
				`/api/fetch_response/?url=${encodeURIComponent(request_url)}`
			).then(show_response.bind(null, response_container));

		});

	}
)();