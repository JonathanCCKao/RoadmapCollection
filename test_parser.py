import unittest
from parser import parse_confluence_table, normalize_date
from generator import generate_mermaid_gantt, generate_chart
from updater import update_html_body

class TestConfluenceRoadmap(unittest.TestCase):
    def test_normalize_date(self):
        self.assertEqual(normalize_date("2026-03-01"), "2026-03-01")
        self.assertEqual(normalize_date("2026/05/15"), "2026-05-15")
        self.assertEqual(normalize_date("2026.08.30"), "2026-08-30")
        self.assertEqual(normalize_date("@2026-10-15"), "2026-10-15")
        self.assertEqual(normalize_date("  2026-11-30  "), "2026-11-30")
        self.assertEqual(normalize_date("TBD"), None)
        self.assertEqual(normalize_date(""), None)
        self.assertEqual(normalize_date(None), None)
        self.assertEqual(normalize_date("2026-02-31"), None) # Invalid date

    def test_parse_table(self):
        html = """
        <table>
          <thead>
            <tr>
              <th>專案名稱 (Project)</th>
              <th>系統架構 (Arch)</th>
              <th>C0 (Kickoff)</th>
              <th>C1 (Design)</th>
              <th>C2 (Alpha)</th>
              <th>C3 (Beta)</th>
              <th>C4 (Pilot)</th>
              <th>C5 (GA)</th>
              <th>狀態與說明</th>
              <th>負責人</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>IES-3100</td>
              <td>Linux 6.x</td>
              <td>2026-03-01</td>
              <td>2026-05-15</td>
              <td>2026-08-30</td>
              <td>2026-10-15</td>
              <td>2026-11-30</td>
              <td>2026-12-30</td>
              <td>🟢 正常</td>
              <td>@Alex</td>
            </tr>
            <tr>
              <td>IES-2000L</td>
              <td>eCos</td>
              <td>2026-01-10</td>
              <td>2026-02-28</td>
              <td>2026-04-30</td>
              <td>2026-06-15</td>
              <td>2026-07-30</td>
              <td>2026-08-15</td>
              <td>🟡 等待 RSTP 修正</td>
              <td>@David</td>
            </tr>
          </tbody>
        </table>
        """
        projects = parse_confluence_table(html)
        self.assertEqual(len(projects), 2)
        
        # Test project 1
        p1 = projects[0]
        self.assertEqual(p1["project"], "IES-3100")
        self.assertEqual(p1["arch"], "Linux 6.x")
        self.assertEqual(p1["milestones"]["c0"], "2026-03-01")
        self.assertEqual(p1["milestones"]["c5"], "2026-12-30")
        self.assertEqual(p1["status"], "🟢 正常")
        self.assertEqual(p1["owner"], "@Alex")

        # Test project 2
        p2 = projects[1]
        self.assertEqual(p2["project"], "IES-2000L")
        self.assertEqual(p2["arch"], "eCos")
        self.assertEqual(p2["milestones"]["c0"], "2026-01-10")
        self.assertEqual(p2["milestones"]["c5"], "2026-08-15")

    def test_parse_rowspan_table(self):
        # HTML content containing two rowspan tables mimicking the user's actual Confluence page
        html = """
        <p>#專案roadmap資訊</p>
        <table>
          <tbody>
            <tr>
              <th scope="col">專案</th>
              <th scope="col">C0-C5</th>
              <th scope="col"><br /></th>
              <th scope="col"><br /></th>
            </tr>
            <tr>
              <td rowspan="5">Axx</td>
              <td><div class="content-wrapper"><p><time datetime="2026-07-01" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-07-06" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-07-13" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-07-20" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-07-27" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td rowspan="5">Bxx</td>
              <td><div class="content-wrapper"><p><time datetime="2026-08-01" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-08-03" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-08-10" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-08-17" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-08-31" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
          </tbody>
        </table>
        <p><br /></p>
        <table>
          <tbody>
            <tr>
              <th>專案</th>
              <th>C0-C5</th>
              <th><br /></th>
              <th><br /></th>
            </tr>
            <tr>
              <td rowspan="5">Cxx</td>
              <td><div class="content-wrapper"><p><time datetime="2026-09-01" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-09-07" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-09-21" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-09-24" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-09-30" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td rowspan="5">Dxx</td>
              <td><div class="content-wrapper"><p><time datetime="2026-11-02" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-11-09" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-11-16" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-11-23" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-12-04" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
          </tbody>
        </table>
        """
        projects = parse_confluence_table(html)
        self.assertEqual(len(projects), 4)

        # Test project Axx
        self.assertEqual(projects[0]["project"], "Axx")
        self.assertEqual(projects[0]["milestones"]["c1"], "2026-07-01")
        self.assertEqual(projects[0]["milestones"]["c5"], "2026-07-27")

        # Test project Bxx
        self.assertEqual(projects[1]["project"], "Bxx")
        self.assertEqual(projects[1]["milestones"]["c1"], "2026-08-01")
        self.assertEqual(projects[1]["milestones"]["c5"], "2026-08-31")

        # Test project Cxx
        self.assertEqual(projects[2]["project"], "Cxx")
        self.assertEqual(projects[2]["milestones"]["c1"], "2026-09-01")
        self.assertEqual(projects[2]["milestones"]["c5"], "2026-09-30")

        # Test project Dxx
        self.assertEqual(projects[3]["project"], "Dxx")
        self.assertEqual(projects[3]["milestones"]["c1"], "2026-11-02")
        self.assertEqual(projects[3]["milestones"]["c5"], "2026-12-04")

    def test_parse_rowspan_table_p_format(self):
        html = """
        <p>#專案roadmap資訊</p>
        <table class="wrapped">
          <tbody>
            <tr>
              <th scope="col">專案</th>
              <th scope="col">P0 - P5</th>
              <th scope="col"><br /></th>
              <th scope="col"><br /></th>
            </tr>
            <tr>
              <td rowspan="6">Axx</td>
              <td><div class="content-wrapper"><p><time datetime="2026-07-01" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-08-04" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-09-09" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-09-18" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-10-30" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div class="content-wrapper"><p><time datetime="2026-12-17" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
          </tbody>
        </table>
        """
        projects = parse_confluence_table(html)
        self.assertEqual(len(projects), 1)
        p = projects[0]
        self.assertEqual(p["project"], "Axx")
        self.assertEqual(p["milestones"]["p0"], "2026-07-01")
        self.assertEqual(p["milestones"]["p1"], "2026-08-04")
        self.assertEqual(p["milestones"]["p5"], "2026-12-17")

    def test_parse_explicit_milestones_table(self):
        html = """
        <p>#專案roadmap資訊</p>
        <table class="wrapped relative-table">
          <tbody>
            <tr>
              <th scope="col">專案</th>
              <th colspan="2" scope="colgroup">Milestone</th>
              <th scope="col"><br /></th>
              <th scope="col"><br /></th>
            </tr>
            <tr>
              <td rowspan="6">Axx</td>
              <td><div><p>P0</p></div></td>
              <td><div><p><time datetime="2026-07-01" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div><p>P1</p></div></td>
              <td><div><p><time datetime="2026-08-04" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div><p>P2</p></div></td>
              <td><div><p><time datetime="2026-09-09" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div><p>P3</p></div></td>
              <td><div><p><time datetime="2026-09-18" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div><p>P4</p></div></td>
              <td><div><p><time datetime="2026-10-30" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
            <tr>
              <td><div><p>P5</p></div></td>
              <td><div><p><time datetime="2026-12-17" /> </p></div></td>
              <td><br /></td>
              <td><br /></td>
            </tr>
          </tbody>
        </table>
        """
        projects = parse_confluence_table(html)
        self.assertEqual(len(projects), 1)
        p = projects[0]
        self.assertEqual(p["project"], "Axx")
        self.assertEqual(p["milestones"]["p0"], "2026-07-01")
        self.assertEqual(p["milestones"]["p1"], "2026-08-04")
        self.assertEqual(p["milestones"]["p5"], "2026-12-17")
        
    def test_generate_mermaid(self):
        projects = [
            {
                "project": "IES-3100",
                "arch": "Linux 6.x",
                "milestones": {
                    "c0": "2026-03-01",
                    "c1": "2026-05-15",
                    "c2": None,
                    "c3": "2026-10-15",
                    "c4": None,
                    "c5": "2026-12-30"
                },
                "status": "🟢 正常",
                "owner": "@Alex"
            }
        ]
        gantt = generate_mermaid_gantt(projects)
        self.assertIn("section IES-3100 (Linux 6.x)", gantt)
        self.assertIn("C0               :milestone, p0_c0, 2026-03-01, 0d", gantt)
        self.assertIn("C1               :milestone, p0_c1, 2026-05-15, 0d", gantt)
        self.assertNotIn("C2 Alpha Release", gantt)
        self.assertIn("C3               :milestone, p0_c3, 2026-10-15, 0d", gantt)
        self.assertIn("C5               :milestone, p0_c5, 2026-12-30, 0d", gantt)

    def test_generate_plantuml(self):
        projects = [
            {
                "project": "IES-3100",
                "arch": "Linux 6.x",
                "milestones": {
                    "c0": "2026-03-01",
                    "c1": "2026-05-15",
                    "c2": None,
                    "c3": "2026-10-15",
                    "c4": None,
                    "c5": "2026-12-30"
                },
                "status": "🟢 正常",
                "owner": "@Alex"
            }
        ]
        gantt = generate_chart(projects, mode="plantuml", update_time="2026-03-01 12:00")
        self.assertIn("@startgantt", gantt)
        self.assertIn("right header <font color=\"#1F4E79\"><b>最後更新時間: 2026-03-01 12:00</b></font>", gantt)
        self.assertIn("project starts 2026-03-01", gantt)
        self.assertIn("projectscale quarterly zoom 3", gantt)
        self.assertIn("today is colored in #E74C3C", gantt)
        self.assertIn("[NOW] happens 2026-03-01", gantt)
        self.assertIn("[NOW] is colored in #E74C3C", gantt)
        self.assertIn("2026-01-01 to 2026-12-31 are colored in #FDF2E9", gantt)
        self.assertIn("[C0] as [IES-3100_c0] starts 2026-03-01 and ends 2026-05-15", gantt)
        self.assertIn("[IES-3100_c0] is colored in #85C1E9", gantt)
        self.assertIn("[IES-3100_c1] displays on same row as [IES-3100_c0]", gantt)
        self.assertIn("@endgantt", gantt)

    def test_parse_status_coloring(self):
        projects = [
            {
                "project": "Axx",
                "arch": "",
                "milestones": {"p0": "2026-07-01", "p1": "2026-08-01"},
                "status": "🔴 嚴重延誤",
                "owner": "John"
            },
            {
                "project": "Bxx",
                "arch": "",
                "milestones": {"p0": "2026-07-01", "p1": "2026-08-01"},
                "status": "🟢 正常",
                "owner": "John"
            },
            {
                "project": "Cxx",
                "arch": "",
                "milestones": {"p0": "2026-07-01", "p1": "2026-08-01"},
                "status": "NEED SUPPORT",
                "owner": "John"
            },
            {
                "project": "Dxx",
                "arch": "",
                "milestones": {"p0": "2026-07-01", "p1": "2026-08-01"},
                "status": "CATCHING UP",
                "owner": "John"
            }
        ]
        gantt = generate_chart(projects, mode="plantuml", update_time="2026-03-01 12:00")
        self.assertIn("right header <font color=\"#1F4E79\"><b>最後更新時間: 2026-03-01 12:00</b></font>", gantt)
        self.assertIn("[NOW] happens 2026-03-01", gantt)
        self.assertIn("[NOW] is colored in #E74C3C", gantt)
        self.assertIn('<font color="#922B21">**Axx**</font>', gantt)
        self.assertIn('<font color="#1E8449">**Bxx**</font>', gantt)
        self.assertIn('<font color="#922B21">**Cxx**</font>', gantt)
        self.assertIn('<font color="#B9770E">**Dxx**</font>', gantt)
        
    def test_update_html_body_replace(self):
        existing_body = (
            "<p>Some content before</p>\n"
            "<ac:structured-macro ac:name=\"mermaid\">\n"
            "  <ac:plain-text-body><![CDATA[\n"
            "    gantt\n"
            "    title Old Chart\n"
            "  ]]></ac:plain-text-body>\n"
            "</ac:structured-macro>\n"
            "<p>Some content after</p>"
        )
        new_mermaid = "gantt\ntitle New Chart"
        updated = update_html_body(existing_body, new_mermaid)
        self.assertIn("title New Chart", updated)
        self.assertNotIn("title Old Chart", updated)
        self.assertIn("Some content before", updated)
        self.assertIn("Some content after", updated)

    def test_update_html_body_insert_top(self):
        existing_body = "<p>Some content before</p>"
        new_mermaid = "gantt\ntitle New Chart"
        updated = update_html_body(existing_body, new_mermaid, insert_position="top")
        self.assertTrue(updated.startswith("<ac:structured-macro"))
        self.assertIn("Some content before", updated)

    def test_update_html_body_insert_bottom(self):
        existing_body = "<p>Some content before</p>"
        new_mermaid = "gantt\ntitle New Chart"
        updated = update_html_body(existing_body, new_mermaid, insert_position="bottom")
        self.assertTrue(updated.endswith("</ac:structured-macro>"))
        self.assertIn("Some content before", updated)

if __name__ == "__main__":
    unittest.main()
