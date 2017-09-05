function calendarRedirect() {
  // Redirects to user-specified 1024-calendar
  var calendarName = window.prompt("Tast inn ditt kalendernavn på ntnu.1024.no. " +
                  "Du blir deretter sendt direkte til din kalender neste gang. ");

  if (calendarName == undefined) {
    return; // Exits function if user didn´t enter a calendar name
  }

  window.location = "/kalender/" + calendarName;
}

function courseHomepageRedirect(course_pk) {
  // Prompts the user for the course's homepage url, redirects to view in order
  // to update the course homepage accordingly
  var homepageURL = window.prompt("Dette faget har ingen lagret hjemmeside. " +
                  "\n\nVennligst tast inn URLen til fagets hjemmeside.");

  if (homepageURL == undefined) {
    return; // Exits function if user didn´t enter a course url
  }

  window.location = "/ny_faghjemmeside/" + course_pk + "/?homepage_url=" + encodeURIComponent(homepageURL);
}

function courseLogoClickEvent(courseHomepage, canEditCourse, courseURL, coursePK, normalLink) {
  const mq = window.matchMedia("(min-width: 500px)");

  if (mq.matches | normalLink) {
    if (courseHomepage === '' & canEditCourse) {
      courseHomepageRedirect(coursePK);
    } else {
      window.location = courseURL;
    }
  } else {
    course = document.getElementById("article-" + coursePK);
	display = course.getElementsByTagName("ul")[0].style.display;
    if (display === "block") {
	  display = course.getElementsByTagName("ul")[0].style.display = "none";
    } else {
	  display = course.getElementsByTagName("ul")[0].style.display = "block";
    }
  }
}

function removeCourseFromStudentPage(course_pk) {
  var confirmation = confirm("Ønsker du å fjerne dette faget fra din hjemmeside?" +
                  "\n\nFaget kan legges til igjen ved å trykke \"Velg fag\" i navigasjonsbaren.");

  if (confirmation) {
    window.location = "/fjern_fag/" + course_pk;
  }
  else {
    return;
  }
}

function redirectToCourseAdmin(url, authenticated, permission) {
  // If the user is authenticated and has edit privileges for the given course,
  // redirect to the Course admin. If the user has not logged in, redirect to
  // the login provider. Else, inform the user that they do not have edit
  // privileges for this specific course.
  if (authenticated && permission) {
    window.location = url;
  } else if (!authenticated) {
   if (window.confirm("Du må være logget inn for å redigere faglenker.\n\n" +
                      "Du vil nå bli logget inn.")) {
     window.location = url;
   }
  } else {
    window.alert("Du kan kun redigere fag du er oppmeldt i.");
  }
}

// Code originally pulled from here: https://www.sitepoint.com/javascript-media-queries/
// Media query event handler
function collapseCoursesOnMobile() {
  if (matchMedia) {
    const mq = window.matchMedia("(min-width: 500px)");
 	mq.addListener(WidthChange);
	WidthChange(mq);
  }
}

// Need to be placed right after the registered event handler above
// Media query change
function WidthChange(mq) {
  if (mq.matches) {
    // window width is at least 500px
	toggleCourseLinkList(hide=false);
  } else {
    // window width is less than 500px
	toggleCourseLinkList(hide=true);
  }
}

function toggleCourseLinkList(hide) {
  var elements = document.getElementsByClassName("course-link-list");
  var homepages = document.getElementsByClassName("homepage-item");

  if (hide) {
	display = "none";
	homepageDisplay = "list-item";
  } else {
	display = "block";
	homepageDisplay = "none";
  }

  for (var i = 0; i < elements.length; i++) {
    elements[i].style.display = display;
  }

  for (var i = 0; i < homepages.length; i++) {
    homepages[i].style.display = homepageDisplay;
  }
}

// Run function after all the course lists have been loaded into the DOM
window.onload = collapseCoursesOnMobile
