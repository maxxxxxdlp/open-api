const get_parameter_value = (parameter_element, parameter_type) =>
  parameter_type === 'string' ?
    parameter_element.getElementsByTagName('input')[0].value :
    (
      parameter_element.getElementsByTagName('input')[0].checked
    ).toString();

const fetch_parameters_data = (parameters) =>
  path_detailed_info.parameters.forEach((parameter, index) => (
    path_detailed_info.parameters[index].value =
      get_parameter_value(parameters[index], parameter.type)
  ));

const create_request_url = () =>
  path_detailed_info.parameters.reduce((request_url, parameter_data) =>
      parameter_data.location === 'path' ?
        request_url.replace(
          `{${parameter_data.name}}`,
          encodeURIComponent(parameter_data.value),
        ) :
        `${request_url}${parameter_data.name}=${encodeURIComponent(
          parameter_data.value,
        )}&`,
    `${path_detailed_info.server}${path_detailed_info.path}?`);

const expose_request_url = (request_url_element, request_url) =>
  request_url_element.classList.remove('hidden') ||
  (
    request_url_element.getElementsByTagName('input')[0].value = request_url
  );

const show_loading_animation = (response_container) =>
  response_container.classList.remove('hidden') ||
  response_container.classList.add('loading');

const show_response = (response_container, response) =>
  response_container.classList.remove('loading') ||
  response.text().then(response_html => (
    response_container.getElementsByClassName(
      'response_content',
    )[0].innerHTML = response_html
  ));

(
  () => {

    const parameters = Object.values(
      document.getElementsByClassName('parameter'),
    );
    const request_url_element =
      document.getElementsByClassName('request_url')[0];
    const response_container = document.getElementById('response');

    document.body.addEventListener('change', (event) => {

      const parameter_examples = event.target.closest('.parameter_examples');
      if (parameter_examples !== null && parameter_examples.value !== '0')
        parameter_examples.parentElement.nextElementSibling.
          getElementsByTagName('input')[0].value =
          parameter_examples.value;

    });

    document.body.addEventListener('click', (event) => {

      if (event.target.closest('.execute_button')) {
        fetch_parameters_data(parameters);
        const request_url = create_request_url();
        expose_request_url(request_url_element, request_url);
        show_loading_animation(response_container);
        fetch(
          `/api/fetch_response/?endpoint=${
            encodeURIComponent(path_detailed_info.path)
          }&url=${encodeURIComponent(request_url)}`,
        ).then(show_response.bind(null, response_container));
      }

      const dictionary_label = event.target.closest('.dictionary_label');
      if (dictionary_label !== null)
        dictionary_label.parentElement.classList.toggle('collapsed');
      else {
        const collapsed = event.target.closest('.collapsed');
        if (collapsed !== null)
          collapsed.classList.toggle('collapsed');
      }

    });

  }
)();