function span_printer_reservations() {
    const ct1 = $('#span_printer_reservations').get(0).getContext("2d");
    const data = JSON.parse($('#span_of_printer_reservations').get(0).textContent);
    Chart.defaults.font.family = "Ubuntu";
    Chart.defaults.font.weight = 500;
    Chart.defaults.font.size = 12.5;

    new Chart(ct1, {
            type: 'bar',
            data: {
                labels: data.map((element)=> element.name),
                datasets: [{
                    label: "How long each printer has been reserved in total",
                    data: data.map((element)=> (element.len)),
                    backgroundColor: [
                        'rgba(249, 65, 68)',
                        'rgb(243, 114, 44)',
                        'rgb(248, 150, 30)',
                        'rgb(249, 132, 74)',
                        'rgb(249, 199, 79)',
                        'rgb(144, 190, 109)',
                        'rgb(67, 170, 139)',
                        'rgb(77, 144, 142)',
                        'rgb(87, 117, 144)',
                        'rgb(39, 125, 161)',
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
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: gettext("*includes 3D printers, Raise3D printers and SLA 3D printers"),
                            }
                        }
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
                    'rgba(3,7,30,0.89)',
                    'rgb(55, 6, 23)',
                    'rgb(106, 4, 15)',
                    'rgb(157, 2, 8)',
                    'rgb(208, 0, 0)',
                    'rgb(220, 47, 2)',
                    'rgb(232, 93, 4)',
                    'rgb(244, 140, 6)',
                    'rgb(250, 163, 7)',
                    'rgb(255, 186, 8)',
                ],
                    fill:
                        true,
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
                                }
                            },
                        x: {
                            title: {
                                display: true,
                                text: gettext("*includes 3D printers, Raise3D printers and SLA 3D printers"),
                                }
                            }
                        },
            plugins:{
                legend: {
                    display: false
                }
            }
        }
    });
}


function span_of_sewingmachine_reservations() {
    const ct3 = $('#span_sewingmachine_reservations').get(0).getContext("2d");
    const data = JSON.parse($('#span_of_sewingmachine_reservations').get(0).textContent);
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
                    'rgb(72, 149, 239)',
                    'rgb(76, 201, 240)',
                ],
                    fill:
                        true,
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
                                    }
                            },
                    },
            plugins:{
                legend: {
                    display: false
                }
            }
        }
    });
}

function sewingmachine_reservations() {
    const ct4 = $('#sewingmachine_reservations').get(0).getContext("2d");
    const data = JSON.parse($('#number_of_sewingmachine_reservations').get(0).textContent);
    new Chart(ct4, {
        type: 'bar',
        data: {
            labels:  data.map((element)=>element.name),
            datasets: [{
                label: "Total number of printer reservations",
                data: data.map((element)=>element.number_of_reservations),
                backgroundColor: [
                'rgb(0, 95, 115)',
                'rgb(10, 147, 150)',
                'rgb(148, 210, 189)',
                'rgb(233, 216, 166)',
                'rgb(238, 155, 0)',
                'rgb(202, 103, 2)',
                'rgb(187, 62, 3)',
                'rgb(174, 32, 18)',
                'rgb(155, 34, 38)',
                ],
                fill:
                    true,
            }]
            },
        options: {
            events: [],
                scales: {
                        y: {
                            beginAtZero: true,
                            display: true,
                            title:
                                {
                                    display: true,
                                    text: gettext("Times reserved"),
                                }
                                },
                    },
            plugins:{
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
                fill:
                    true,
            }]
            },
        options: {
            events: [],
                scales:
                    {
                        y: {
                            beginAtZero: true,
                            display: true,
                            title:
                                {
                                    display: true,
                                    text: gettext("Hours reserved"),
                                }
                                },
                        x: {
                            title: {
                                display: true,
                                text: gettext("*includes 3D printers, Raise3D printers and SLA 3D printers"),
                            }
                        }
                    },
            plugins:{
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
                  display: false

              },
              x:{
                  title: {
                        display: true,
                        text: gettext("Time of day"),
                    }

              }
          }
      }
  });
}

printer_reservations();
span_printer_reservations();
span_of_sewingmachine_reservations();
sewingmachine_reservations();
longest_printer_reservations();
timespan();
