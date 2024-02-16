
Chart.defaults.font.family = "Ubuntu";
Chart.defaults.font.weight = 500;
Chart.defaults.font.size = 12.5;

function span_printer_reservations() {
    const ct1 = $('#span_printer_reservations').get(0).getContext("2d");
    const data = JSON.parse($('#span_of_printer_reservations').get(0).textContent);

    new Chart(ct1, {
            type: 'bar',
            data: {
                labels: data.map((element)=> element.name),
                datasets: [{
                    label: "How long each printer has been reserved in total",
                    data: data.map((element)=> (element.len)),
                    backgroundColor: [
                        'rgb(223, 146, 57)',
                        'rgb(246, 171, 52)',
                        'rgb(247, 181, 40)',
                        'rgb(248, 200, 17)',
                        'rgba(250, 210, 59)',
                        'rgb(248, 200, 17)',
                        'rgb(247, 181, 40)',
                        'rgb(246, 171, 52)',
                        'rgb(223, 146, 57)',
                    ],
                    fill: true,
                }]
            },
            options: {
                events: [],
                scales: {
                    y: {
                        beginAtZero: true,
                        display: true,
                        title: {
                            display: true,
                            text: gettext("Hours reserved"),
                        },
                        ticks: {
                            stepSize: 1
                        },
                    },
                    },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
}


function printer_reservations() {
    const ct2 = $('#printer_reservations').get(0).getContext("2d");
    const data = JSON.parse($('#number_of_printer_reservations').get(0).textContent);
    new Chart(ct2, {
        type: 'bar',
        data: {
            labels: data.map((element)=>element.name),
            datasets: [{
                label: "Total number of printer reservations",
                data: data.map((element)=>element.number_of_reservations),
                backgroundColor: [
                    'rgb(106, 4, 15)',
                    'rgb(157, 2, 8)',
                    'rgb(208, 0, 0)',
                    'rgb(220, 47, 2)',
                    'rgb(232, 93, 4)',
                    'rgb(244, 140, 6)',
                    'rgb(232, 93, 4)',
                    'rgb(220, 47, 2)',
                    'rgb(208, 0, 0)',
                    'rgb(157, 2, 8)',
                    'rgb(106, 4, 15)',
                ],
                    fill: true,
                }]
            },
        options: {
            events: [],
                scales: {
                        y: {
                            beginAtZero: true,
                            display: true,
                            title: {
                                display: true,
                                text: gettext("Times reserved"),
                                },
                            ticks: {
                                stepSize: 1
                            },
                        },
                        },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}


function span_of_sewing_machine_reservations() {
    const ct3 = $('#span_sewing_machine_reservations').get(0).getContext("2d");
    const data = JSON.parse($('#span_of_sewing_machine_reservations').get(0).textContent);
    new Chart(ct3, {
        type: 'bar',
        data: {
            labels: data.map((element)=> element.name),
            datasets: [{
                label: "Total number of printer reservations",
                data: data.map((element)=> element.len),
                backgroundColor: [
                    'rgb(247, 37, 133)',
                    'rgb(181, 23, 158)',
                    'rgb(114, 9, 183)',
                    'rgb(86, 11, 173)',
                    'rgb(72, 12, 168)',
                    'rgb(58, 12, 163)',
                    'rgb(63, 55, 201)',
                    'rgb(67, 97, 238)',
                    'rgb(76, 201, 240)',
                ],
                    fill: true,
                }]
            },
        options: {
            events: [],
                scales: {
                        y: {
                            beginAtZero: true,
                            display: true,
                            title: {
                                    display: true,
                                    text: gettext("Hours reserved"),
                                },
                            ticks: {
                                stepSize: 1
                            },
                        },
                    },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function sewing_machine_reservations() {
    const ct4 = $('#sewing_machine_reservations').get(0).getContext("2d");
    const data = JSON.parse($('#number_of_sewing_machine_reservations').get(0).textContent);
    new Chart(ct4, {
        type: 'bar',
        data: {
            labels:  data.map((element)=>element.name),
            datasets: [{
                label: "Total number of printer reservations",
                data: data.map((element)=>element.number_of_reservations),
                backgroundColor: [
                    'rgb(0,235,179)',

                    '#00EBB3',
                    '#03C1A1',
                    '#06978F',
                    '#096C7C',
                    '#0C426A',
                    '#096C7C',
                    '#06978F',
                    '#03C1A1',
                ],
                fill: true,
            }]
            },
        options: {
            events: [],
                scales: {
                        y: {
                            beginAtZero: true,
                            display: true,
                            title: {
                                    display: true,
                                    text: gettext("Times reserved"),
                            },
                            ticks: {
                                stepSize: 1
                            },
                        },
                    },
            plugins: {
                legend: {
                    display: false
                }
            }
        }

});
}



function longest_printer_reservations() {
    const ct5 = $('#3_longest_printer_reservations').get(0).getContext("2d");
    const data = JSON.parse($('#longest_printer_reservations').get(0).textContent);
    new Chart(ct5, {
        type: 'bar',
        data: {
            labels: data.map((element)=> element.name),
            datasets: [{
                label: "Total number of printer reservations",
                data: data.map((element)=> element.len),
                backgroundColor: [
                'rgb(212,175,55)',
                'rgb(192,192,192)',
                'rgb(205,127,50)',
                ],
                fill: true,
            }]
            },
        options: {
            events: [],
                scales: {
                        y: {
                            beginAtZero: true,
                            display: true,
                            title: {
                                    display: true,
                                    text: gettext("Hours reserved"),
                            },
                            ticks: {
                                stepSize: 1
                                },
                            },
                    },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}


function timespan(){
      const ct6 = $('#timespan').get(0).getContext("2d");
      const data = JSON.parse($('#time').get(0).textContent);
      new Chart(ct6, {
      type: 'line',
      data: {
        labels : Object.keys(data),
          datasets: [{
            label: gettext("Traffic"),
            data : Object.values(data),
            backgroundColor: 'rgb(236,212,119)',
            borderColor: 'rgb(248, 200, 17)',
            borderWidth: 2,
            fill: true,
          }]
      },
      options: {
          events: [],
          responsive:true,
          scales: {
              y: {
                  beginAtZero: true,
                  title: {
                      display: true,
                      text: gettext("Activity at the workshop"),
                  },
                  ticks: {
                      display: false,
                  }

              },
              x:{
                  title: {
                        display: true,
                        text: gettext("Time of day"),
                    },
                  ticks: {
                      maxRotation: 0,
                      minRotation: 0
                  }
              }
          }
      }
  });
}

printer_reservations();
span_printer_reservations();
span_of_sewing_machine_reservations();
sewing_machine_reservations();
longest_printer_reservations();
timespan();
