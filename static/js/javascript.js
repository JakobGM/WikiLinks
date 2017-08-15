// Redirects to user-specified 1024-calendar
function calendarRedirect() {
  var calendarName = window.prompt("Tast inn ditt kalendernavn på ntnu.1024.no. " +
                  "Du blir deretter sendt direkte til din kalender neste gang. ");

  if (calendarName == undefined) {
    return; // Exits function if user didn´t enter a calendar name
  }

  window.location = "/kalender/" + calendarName;
}

// Prompts the user for the course's homepage url, redirects to view in order
// to update the course homepage accordingly
function courseHomepageRedirect(course_pk) {
  var homepageURL = window.prompt("Dette faget har ingen lagret hjemmeside. " +
                  "Vennligst tast inn URLen for å lagre en ny en.");

  if (homepageURL == undefined) {
    return; // Exits function if user didn´t enter a course url
  }

  window.location = "/ny_faghjemmeside/" + course_pk + "/?homepage_url=" + homepageURL;
}
