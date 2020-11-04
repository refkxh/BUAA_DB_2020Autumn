from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from flask_login import current_user

from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash

from .auth import check_permission

from jiaowu import validators

from jiaowu.db_base import get_db

bp = Blueprint('student', __name__, url_prefix='/student')


@bp.route('/', methods=('GET',))
@check_permission('Student', False)
def index():
    return redirect(url_for('student.update_stu', sno=current_user.no))


@bp.route('/update_stu', methods=('GET', 'POST'))
@check_permission('Student', False)
def update_stu():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        spwd = request.form['spwd']
        sname = request.form['sname']
        ssex = request.form['ssex']
        sid = request.form['sid']
        sgrade = request.form['sgrade']
        sdept = request.form['sdept']
        stel = request.form['stel']
        smail = request.form['smail']

        try:
            validators.Student.sname(sname)
            validators.Student.spwd(spwd, True)
            validators.Student.ssex(ssex)
            validators.Student.sid(sid, cur_sno=current_user.no)
            validators.Student.sgrade(sgrade)
            validators.Student.sdept(sdept)
            validators.Student.stel(stel)
            validators.Student.smail(smail)

            cursor.callproc('update_student', (current_user.no, sname, ssex, sid, sgrade, sdept, stel, smail))

            if len(spwd) > 0:
                cursor.callproc('update_student_pwd', (current_user.no, generate_password_hash(spwd)))

            db.commit()
            cursor.close()
            flash('修改成功！')
        except validators.ValidateException as e:
            flash(e.info)

        return redirect(url_for('student.update_stu', sno=current_user.no))
    else:
        cursor.execute(
            'select sno, sname, ssex, sid, sgrade, sdept, stel, smail'
            ' from student'
            ' where sno = %s',
            (current_user.no,)
        )
        student = cursor.fetchone()
        cursor.close()
        if student is None:
            abort(404)
        return render_template('student/update_stu.html', student=student)


@bp.route('/list_unselected_courses', methods=('GET',))
@check_permission('Student', False)
def list_unselected_courses():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('select * from course where cno not in '
                   '(select cno from student_course where sno = %s) '
                   'order by cno', (current_user.no,))
    courses = cursor.fetchall()
    cursor.close()
    return render_template('student/list_unselected_courses.html', courses=courses)


@bp.route('/select_course/<int:cno>', methods=('POST',))
@check_permission('Student', False)
def select_course(cno):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('select * from student_course where sno = %s and cno = %s', (current_user.no, cno))
    if cursor.fetchone() is not None:
        flash('您已选修过该课程！')
    else:
        cursor.callproc('select_course', (current_user.no, cno))
        flash('选课成功！')
    db.commit()
    cursor.close()
    return redirect(url_for('student.list_unselected_courses'))


@bp.route('/list_selected_courses', methods=('GET',))
@check_permission('Student', False)
def list_selected_courses():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('select course.cno cno, cname, ctype, ccredit, cdept, ccap, cselect, score '
                   'from course, student_course '
                   'where course.cno = student_course.cno and sno = %s '
                   'order by cno', (current_user.no,))
    courses = cursor.fetchall()
    cursor.close()
    return render_template('student/list_selected_courses.html', courses=courses)


@bp.route('/unselect_course/<int:cno>', methods=('POST',))
@check_permission('Student', False)
def unselect_course(cno):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('select * from student_course where sno = %s and cno = %s', (current_user.no, cno))
    if cursor.fetchone() is None:
        flash('您并未选修过该课程！')
    else:
        cursor.callproc('unselect_course', (current_user.no, cno))
        flash('退课成功！')
    db.commit()
    cursor.close()
    return redirect(url_for('student.list_selected_courses'))
